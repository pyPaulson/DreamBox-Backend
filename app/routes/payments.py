from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import uuid4
import os, requests
from app.core.database import get_db
from app.models import user as user_model
from app.models.goals import SafeLockAccount
from app.models.transactions import DepositTransaction
from app.dependencies.auth import get_current_user
from app.models.goals import SafeLockAccount, MyGoalAccount, EmergencyFund, FlexiAccount

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/init-deposit", status_code=201)
def initialize_deposit(
    amount: float,
    account_type: str,
    goal_id: str = None,
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    account_type = account_type.lower()
    valid_account_types = ["flexi", "emergency", "safelock"]
    if account_type not in valid_account_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid account type. Must be 'flexi', 'emergency', or 'safelock'."
        )

    # Validate goal_id if needed
    if account_type in ["safelock", "emergency"]:
        if not goal_id:
            raise HTTPException(status_code=400, detail="goal_id is required for this account type")

        if account_type == "safelock":
            goal = db.query(SafeLockAccount).filter_by(id=goal_id, user_id=current_user.id).first()
            if not goal:
                raise HTTPException(status_code=404, detail="SafeLock goal not found")
        elif account_type == "emergency":
            goal = db.query(SafeLockAccount).filter_by(id=goal_id, user_id=current_user.id).first()
            if not goal or not goal.has_emergency_fund:
                raise HTTPException(status_code=400, detail="This goal does not have emergency fund enabled.")

    # ✅ PAYSTACK SETUP
    paystack_secret_key = os.getenv("PAYSTACK_SECRET_KEY")
    if not paystack_secret_key:
        raise HTTPException(status_code=500, detail="Paystack secret key not configured")

    headers = {
        "Authorization": f"Bearer {paystack_secret_key}",
        "Content-Type": "application/json"
    }

    callback_url = "http://your-app.com/payment/callback"  # update to your real callback URL

    payload = {
        "email": current_user.email,
        "amount": int(amount * 100),  # Convert to kobo
        "callback_url": callback_url,
        "metadata": {
            "account_type": account_type,
            "goal_id": goal_id,
            "user_id": str(current_user.id)
        }
    }

    # ✅ Send request to Paystack
    response = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to initialize payment with Paystack")

    paystack_data = response.json().get("data")

    # ✅ Ensure we return the correct data to frontend
    return {
        "authorization_url": paystack_data["authorization_url"],
        "reference": paystack_data["reference"]
    }

        

    # Rest of your initialization code remains the same...

@router.get("/verify-deposit")
def verify_deposit(
    reference: str = Query(..., description="Paystack transaction reference"),
    db: Session = Depends(get_db),
    current_user: user_model.User = Depends(get_current_user),
):
    # Step 1: Look up the transaction by reference
    deposit = db.query(DepositTransaction).filter_by(reference=reference, user_id=current_user.id).first()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if deposit.is_successful:
        return {"message": "Transaction has already been verified and processed."}

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

    # Step 3: Mark transaction as successful
    deposit.is_successful = True

    # FIX 2: Update account balances based on account_type
    if deposit.account_type == "safelock":
        safelock = db.query(SafeLockAccount).filter_by(id=deposit.goal_id, user_id=current_user.id).first()
        if not safelock:
            raise HTTPException(status_code=404, detail="SafeLock goal not found")

        # If emergency fund is enabled, split the amount
        if safelock.has_emergency_fund and safelock.emergency_fund_percentage:
            emergency_share = (safelock.emergency_fund_percentage / 100.0) * deposit.amount
            safelock_share = deposit.amount - emergency_share

            safelock.current_amount += safelock_share

            # Update EmergencyFund balance
            emergency = db.query(EmergencyFund).filter_by(user_id=current_user.id).first()
            if not emergency:
                emergency = EmergencyFund(
                    user_id=current_user.id, 
                    balance=emergency_share, 
                    percentage=safelock.emergency_fund_percentage
                )
                db.add(emergency)
            else:
                emergency.balance += emergency_share
        else:
            # No emergency split
            safelock.current_amount += deposit.amount

    elif deposit.account_type == "emergency":
        # FIX 3: Handle emergency fund deposits properly
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
            # FIX 4: Create flexi account if it doesn't exist
            flexi = FlexiAccount(user_id=current_user.id, balance=deposit.amount)
            db.add(flexi)
        else:
            flexi.balance += deposit.amount

    else:
        raise HTTPException(status_code=400, detail="Invalid account type")
    
    db.commit()

    return {
        "message": "Deposit verified and balance updated successfully",
        "amount": deposit.amount,
        "account_type": deposit.account_type,
        "reference": deposit.reference
    }
