from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.transactions import (
    TransactionResponse, TransactionFilter, AccountStatement,
    AccountSummary, TransactionSummary, AccountType, TransactionType
)
from app.utils.transactions import TransactionService
from app.models.goals import SafeLockAccount, MyGoalAccount, EmergencyFund, FlexiAccount

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    account_type: Optional[AccountType] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    goal_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user transactions with optional filters"""
    
    filters = TransactionFilter(
        account_type=account_type,
        transaction_type=transaction_type,
        goal_id=goal_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    transactions = TransactionService.get_user_transactions(
        db=db,
        user_id=str(current_user.id),
        filters=filters
    )
    
    return [TransactionResponse.model_validate(t) for t in transactions]

@router.get("/recent", response_model=List[TransactionResponse])
def get_recent_transactions(
    limit: int = Query(5, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent transactions for home screen"""
    
    transactions = TransactionService.get_recent_transactions(
        db=db,
        user_id=str(current_user.id),
        limit=limit
    )
    
    return [TransactionResponse.model_validate(t) for t in transactions]

@router.get("/statement", response_model=AccountStatement)
def get_account_statement(
    account_type: Optional[AccountType] = Query(None),
    transaction_type: Optional[TransactionType] = Query(None),
    goal_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete account statement with filters"""
    
    filters = TransactionFilter(
        account_type=account_type,
        transaction_type=transaction_type,
        goal_id=goal_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    statement = TransactionService.get_account_statement(
        db=db,
        user_id=str(current_user.id),
        filters=filters
    )
    
    return AccountStatement(
        user_id=statement.user_id,
        account_balance=statement.account_balance,
        total_deposits=statement.total_deposits,
        total_withdrawals=statement.total_withdrawals,
        transaction_count=statement.transaction_count,
        transactions=[TransactionResponse.model_validate(t) for t in statement.transactions]
    )

@router.get("/summary", response_model=TransactionSummary)
def get_transaction_summary(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction summary for specified period"""
    
    summary = TransactionService.get_transaction_summary(
        db=db,
        user_id=str(current_user.id),
        days=days
    )
    
    return summary

@router.get("/account-summary", response_model=AccountSummary)
def get_account_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get account summary with all balances and recent transactions"""
    
    # Calculate balances
    safelock_balance = sum([
        sl.current_amount for sl in 
        db.query(SafeLockAccount).filter(SafeLockAccount.user_id == current_user.id).all()
    ])
    
    mygoal_balance = sum([
        mg.current_amount for mg in 
        db.query(MyGoalAccount).filter(MyGoalAccount.user_id == current_user.id).all()
    ])
    
    emergency_fund = db.query(EmergencyFund).filter(EmergencyFund.user_id == current_user.id).first()
    emergency_balance = emergency_fund.balance if emergency_fund else 0.0
    
    flexi_account = db.query(FlexiAccount).filter(FlexiAccount.user_id == current_user.id).first()
    flexi_balance = flexi_account.balance if flexi_account else 0.0
    
    total_balance = safelock_balance + mygoal_balance + emergency_balance + flexi_balance
    
    # Get recent transactions
    recent_transactions = TransactionService.get_recent_transactions(
        db=db,
        user_id=str(current_user.id),
        limit=10
    )
    
    return AccountSummary(
        total_balance=total_balance,
        safelock_balance=safelock_balance,
        mygoal_balance=mygoal_balance,
        emergency_balance=emergency_balance,
        flexi_balance=flexi_balance,
        recent_transactions=[TransactionResponse.model_validate(t) for t in recent_transactions]
    )

@router.get("/goals", response_model=List[dict])
def get_user_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user goals for filtering options"""
    
    goals = []
    
    # SafeLock goals
    safelocks = db.query(SafeLockAccount).filter(SafeLockAccount.user_id == current_user.id).all()
    for sl in safelocks:
        goals.append({
            "id": str(sl.id),
            "name": sl.goal_name,
            "type": "safelock",
            "target_amount": sl.target_amount,
            "current_amount": sl.current_amount
        })
    
    # MyGoal goals
    mygoals = db.query(MyGoalAccount).filter(MyGoalAccount.user_id == current_user.id).all()
    for mg in mygoals:
        goals.append({
            "id": str(mg.id),
            "name": mg.goal_name,
            "type": "mygoal",
            "target_amount": mg.target_amount,
            "current_amount": mg.current_amount
        })
    
    return goals