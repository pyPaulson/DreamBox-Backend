from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from uuid import uuid4
import os, requests
from app.core.database import get_db
from app.models import user as user_model
from app.models.goals import SafeLockAccount, MyGoalAccount, EmergencyFund, FlexiAccount
from app.models.transactions import DepositTransaction
from app.dependencies.auth import get_current_user
from app.utils.transactions import TransactionService
from app.models.transactions import TransactionType, AccountType
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])

class DepositRequest(BaseModel):
    amount: float
    account_type: str
    goal_id: Optional[str] = None

@router.post("/init-deposit", status_code=201)
def initialize_deposit(
    deposit_request: DepositRequest,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    amount = deposit_request.amount
    account_type = deposit_request.account_type.lower()
    goal_id = deposit_request.goal_id
    
    valid_account_types = ["flexi", "emergency", "safelock", "mygoal"]
    if account_type not in valid_account_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid account type. Must be 'flexi', 'emergency', 'mygoal' or 'safelock'."
        )

    # Validate goal_id if needed
    goal_name = None
    if account_type in ["safelock", "mygoal"]:
        if not goal_id:
            raise HTTPException(status_code=400, detail="goal_id is required for this account type")

        if account_type == "safelock":
            goal = db.query(SafeLockAccount).filter_by(id=goal_id, user_id=current_user.id).first()
            if not goal:
                raise HTTPException(status_code=404, detail="SafeLock goal not found")
            
            if goal.current_amount + amount > goal.target_amount:
                raise HTTPException(status_code=400, detail="Deposit exceeds target amount for SafeLock")
            goal_name = goal.goal_name
            
        elif account_type == "mygoal":
            goal = db.query(MyGoalAccount).filter_by(id=goal_id, user_id=current_user.id).first()
            if not goal:
                raise HTTPException(status_code=404, detail="MyGoal goal not found")

            if goal.current_amount + amount > goal.target_amount:
                raise HTTPException(status_code=400, detail="Deposit exceeds target amount for MyGoal")
            goal_name = goal.goal_name

    # ✅ PAYSTACK SETUP
    paystack_secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    if not paystack_secret_key:
        raise HTTPException(status_code=500, detail="Paystack secret key not configured")

    headers = {
        "Authorization": f"Bearer {paystack_secret_key}",
        "Content-Type": "application/json"
    }

    # Generate a unique reference for this transaction
    reference = f"dep_{uuid4().hex[:12]}"
    callback_url = "http://your-app.com/payment/callback"  # update to your real callback URL

    payload = {
        "email": current_user.email,
        "amount": int(amount * 100),  # Convert to kobo
        "reference": reference,
        "callback_url": callback_url,
        "metadata": {
            "account_type": account_type,
            "goal_id": goal_id,
            "user_id": str(current_user.id),
            "goal_name": goal_name
        }
    }

    # ✅ Send request to Paystack
    response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to initialize payment with Paystack")

    paystack_data = response.json().get("data")

    try:
        # ✅ CREATE TRANSACTION RECORD using the new Transaction service
        transaction = TransactionService.create_transaction(
            db=db,
            user_id=str(current_user.id),
            transaction_type=TransactionType.DEPOSIT,
            account_type=AccountType(account_type),
            amount=amount,
            goal_id=goal_id,
            reference=reference,
            description=f"Deposit to {goal_name or account_type} account"
        )
        
        # Also create the old DepositTransaction for backward compatibility
        deposit = DepositTransaction(
            user_id=current_user.id,
            amount=amount,
            account_type=account_type,
            goal_id=goal_id,
            reference=reference,
            is_successful=False
        )
        db.add(deposit)
        db.commit()
        
        logger.info(f"Created transaction record {transaction.id} for user {current_user.id}")

    except Exception as e:
        logger.error(f"Failed to create transaction record: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to initialize transaction")

    # ✅ Ensure we return the correct data to frontend
    return {
        "authorization_url": paystack_data["authorization_url"],
        "reference": reference,
        "message": "Payment initialized successfully"
    }

@router.get("/verify-deposit")
def verify_deposit(
    reference: str,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    # Step 1: Look up the transaction by reference
    deposit = db.query(DepositTransaction).filter_by(reference=reference, user_id=current_user.id).first()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if deposit.is_successful:
        return {
            "message": "Transaction has already been verified and processed.",
            "amount": deposit.amount,
            "account_type": deposit.account_type,
            "reference": deposit.reference,
            "success": True
        }

    # Step 2: Verify payment with Paystack
    headers = {
        "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}"
    }
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to verify transaction with Paystack")

    data = response.json().get("data")

    if data["status"] != "success":
        raise HTTPException(status_code=400, detail="Transaction not successful yet")

    # Verify the amount matches (convert from kobo to naira/cedi)
    expected_amount = int(deposit.amount * 100)
    if data["amount"] != expected_amount:
        raise HTTPException(status_code=400, detail="Transaction amount mismatch")

    # Step 3: Mark transaction as successful
    deposit.is_successful = True

    # Step 4: Update account balances based on account_type
    emergency_fund_amount = 0.0
    main_goal_amount = deposit.amount
    
    try:
        if deposit.account_type == "safelock":
            safelock = db.query(SafeLockAccount).filter_by(id=deposit.goal_id, user_id=current_user.id).first()
            if not safelock:
                raise HTTPException(status_code=404, detail="SafeLock goal not found")
            
            if safelock.current_amount + deposit.amount > safelock.target_amount:
                raise HTTPException(status_code=400, detail="Deposit exceeds target amount for SafeLock goal")

            # If emergency fund is enabled, split the amount
            if safelock.has_emergency_fund and safelock.emergency_fund_percentage:
                emergency_fund_amount = (safelock.emergency_fund_percentage / 100.0) * deposit.amount
                main_goal_amount = deposit.amount - emergency_fund_amount

                safelock.current_amount += main_goal_amount

                # Update EmergencyFund balance
                emergency = db.query(EmergencyFund).filter_by(user_id=current_user.id).first()
                if not emergency:
                    emergency = EmergencyFund(
                        user_id=current_user.id, 
                        balance=emergency_fund_amount
                    )
                    db.add(emergency)
                else:
                    emergency.balance += emergency_fund_amount
            else:
                # No emergency split
                safelock.current_amount += deposit.amount

        elif deposit.account_type == "emergency":
            emergency = db.query(EmergencyFund).filter_by(user_id=current_user.id).first()
            if not emergency:
                # Create emergency fund if it doesn't exist
                emergency = EmergencyFund(user_id=current_user.id, balance=deposit.amount)
                db.add(emergency)
            else:
                emergency.balance += deposit.amount

        elif deposit.account_type == "flexi":
            flexi = db.query(FlexiAccount).filter_by(user_id=current_user.id).first()
            if not flexi:
                # Create flexi account if it doesn't exist
                flexi = FlexiAccount(user_id=current_user.id, balance=deposit.amount)
                db.add(flexi)
            else:
                flexi.balance += deposit.amount

        elif deposit.account_type == "mygoal":
            my_goal = db.query(MyGoalAccount).filter_by(id=deposit.goal_id, user_id=current_user.id).first()
            if not my_goal:
                raise HTTPException(status_code=404, detail="MyGoal not found")
            
            if my_goal.current_amount + deposit.amount > my_goal.target_amount:
                raise HTTPException(status_code=400, detail="Deposit exceeds target amount for MyGoal")
            
            my_goal.current_amount += deposit.amount

        else:
            raise HTTPException(status_code=400, detail="Invalid account type")
        
        # Update the transaction record to completed
        from app.models.transactions import Transaction, TransactionStatus
        transaction = db.query(Transaction).filter_by(reference=reference, user_id=current_user.id).first()
        if transaction:
            transaction = TransactionService.complete_transaction(
                db=db,
                transaction_id=str(transaction.id),
                emergency_fund_amount=emergency_fund_amount,
                main_goal_amount=main_goal_amount
            )
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Successfully processed deposit {reference} for user {current_user.id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update account balance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update account balance: {str(e)}")

    return {
        "message": "Deposit verified and balance updated successfully",
        "amount": deposit.amount,
        "account_type": deposit.account_type,
        "emergency_fund_amount": emergency_fund_amount,
        "main_goal_amount": main_goal_amount,
        "reference": deposit.reference,
        "success": True
    }