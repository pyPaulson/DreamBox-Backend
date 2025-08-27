from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.goals import SafeLockAccount, MyGoalAccount, EmergencyFund, FlexiAccount
from app.models.transactions import Transaction, TransactionType, AccountType, TransactionStatus
from app.schemas.transactions import TransactionResponse, AccountSummary

router = APIRouter(prefix="/account", tags=["Account Statement"])

@router.get("/summary", response_model=Dict[str, Any])
def get_comprehensive_account_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive account summary including:
    - All account balances
    - Goal progress
    - Recent transactions
    - Financial statistics
    """
    
    # Get all account balances
    safelocks = db.query(SafeLockAccount).filter(SafeLockAccount.user_id == current_user.id).all()
    mygoals = db.query(MyGoalAccount).filter(MyGoalAccount.user_id == current_user.id).all()
    emergency_fund = db.query(EmergencyFund).filter(EmergencyFund.user_id == current_user.id).first()
    flexi_account = db.query(FlexiAccount).filter(FlexiAccount.user_id == current_user.id).first()
    
    # Calculate balances
    safelock_balance = sum(sl.current_amount for sl in safelocks)
    mygoal_balance = sum(mg.current_amount for mg in mygoals)
    emergency_balance = emergency_fund.balance if emergency_fund else 0.0
    flexi_balance = flexi_account.balance if flexi_account else 0.0
    total_balance = safelock_balance + mygoal_balance + emergency_balance + flexi_balance
    
    # Get goal progress
    safelock_goals = []
    for sl in safelocks:
        progress_percentage = (sl.current_amount / sl.target_amount * 100) if sl.target_amount > 0 else 0
        days_remaining = (sl.target_date - datetime.now().date()).days if sl.target_date else None
        
        safelock_goals.append({
            "id": str(sl.id),
            "name": sl.goal_name,
            "target_amount": sl.target_amount,
            "current_amount": sl.current_amount,
            "progress_percentage": round(progress_percentage, 2),
            "days_remaining": days_remaining,
            "target_date": sl.target_date,
            "has_emergency_fund": sl.has_emergency_fund,
            "emergency_fund_percentage": sl.emergency_fund_percentage
        })
    
    mygoal_goals = []
    for mg in mygoals:
        progress_percentage = (mg.current_amount / mg.target_amount * 100) if mg.target_amount > 0 else 0
        days_remaining = (mg.target_date - datetime.now().date()).days if mg.target_date else None
        
        mygoal_goals.append({
            "id": str(mg.id),
            "name": mg.goal_name,
            "target_amount": mg.target_amount,
            "current_amount": mg.current_amount,
            "progress_percentage": round(progress_percentage, 2),
            "days_remaining": days_remaining,
            "target_date": mg.target_date
        })
    
    # Get recent transactions (last 10)
    recent_transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Get monthly statistics
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_stats = (
        db.query(
            func.sum(Transaction.amount).label('total_deposits'),
            func.count(Transaction.id).label('transaction_count')
        )
        .filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == TransactionType.DEPOSIT,
                Transaction.status == TransactionStatus.SUCCESSFUL,
                Transaction.created_at >= current_month
            )
        )
        .first()
    )
    
    monthly_deposits = monthly_stats.total_deposits or 0.0
    monthly_transactions = monthly_stats.transaction_count or 0
    
    return {
        "account_balances": {
            "total_balance": total_balance,
            "safelock_balance": safelock_balance,
            "mygoal_balance": mygoal_balance,
            "emergency_balance": emergency_balance,
            "flexi_balance": flexi_balance
        },
        "goals": {
            "safelock_goals": safelock_goals,
            "mygoal_goals": mygoal_goals,
            "total_goals": len(safelock_goals) + len(mygoal_goals)
        },
        "recent_transactions": [
            {
                "id": str(t.id),
                "transaction_type": t.transaction_type,
                "account_type": t.account_type,
                "amount": t.amount,
                "status": t.status,
                "description": t.description,
                "goal_name": t.goal_name,
                "created_at": t.created_at,
                "reference": t.reference
            }
            for t in recent_transactions
        ],
        "monthly_statistics": {
            "total_deposits": monthly_deposits,
            "transaction_count": monthly_transactions
        },
        "account_status": {
            "has_emergency_fund": emergency_fund is not None,
            "has_flexi_account": flexi_account is not None,
            "active_goals": len([g for g in safelock_goals + mygoal_goals if g["days_remaining"] and g["days_remaining"] > 0])
        }
    }

@router.get("/statement", response_model=Dict[str, Any])
def get_detailed_account_statement(
    start_date: Optional[datetime] = Query(None, description="Start date for statement period"),
    end_date: Optional[datetime] = Query(None, description="End date for statement period"),
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    goal_id: Optional[UUID] = Query(None, description="Filter by specific goal"),
    limit: int = Query(100, le=500, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed account statement with:
    - Opening and closing balances
    - All transactions in period
    - Summary statistics
    - Goal-specific breakdowns
    """
    
    # Set default date range if not provided (last 30 days)
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # Build query filters
    filters = [Transaction.user_id == current_user.id]
    
    if account_type:
        filters.append(Transaction.account_type == account_type)
    
    if goal_id:
        filters.append(Transaction.goal_id == goal_id)
    
    filters.append(Transaction.created_at >= start_date)
    filters.append(Transaction.created_at <= end_date)
    
    # Get transactions
    transactions = (
        db.query(Transaction)
        .filter(and_(*filters))
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    # Calculate opening balance (sum of all transactions before start_date)
    opening_balance_query = (
        db.query(func.sum(Transaction.amount))
        .filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.transaction_type == TransactionType.DEPOSIT,
                Transaction.status == TransactionStatus.SUCCESSFUL,
                Transaction.created_at < start_date
            )
        )
    )
    
    if account_type:
        opening_balance_query = opening_balance_query.filter(Transaction.account_type == account_type)
    
    opening_balance = opening_balance_query.scalar() or 0.0
    
    # Calculate period statistics
    period_stats = (
        db.query(
            func.sum(Transaction.amount).label('total_deposits'),
            func.count(Transaction.id).label('total_transactions'),
            func.avg(Transaction.amount).label('average_amount')
        )
        .filter(and_(*filters))
        .first()
    )
    
    # Get account balances at end of period
    current_balances = get_current_balances(current_user.id, db)
    
    # Group transactions by account type
    transactions_by_account = {}
    for t in transactions:
        account = t.account_type.value
        if account not in transactions_by_account:
            transactions_by_account[account] = []
        
        transactions_by_account[account].append({
            "id": str(t.id),
            "transaction_type": t.transaction_type,
            "amount": t.amount,
            "status": t.status,
            "description": t.description,
            "goal_name": t.goal_name,
            "created_at": t.created_at,
            "reference": t.reference,
            "emergency_fund_amount": t.emergency_fund_amount,
            "main_goal_amount": t.main_goal_amount
        })
    
    return {
        "statement_period": {
            "start_date": start_date,
            "end_date": end_date,
            "opening_balance": opening_balance,
            "closing_balance": current_balances.get("total_balance", 0.0)
        },
        "period_statistics": {
            "total_deposits": period_stats.total_deposits or 0.0,
            "total_transactions": period_stats.total_transactions or 0,
            "average_transaction_amount": round(period_stats.average_amount or 0.0, 2)
        },
        "current_balances": current_balances,
        "transactions": {
            "total_count": len(transactions),
            "by_account_type": transactions_by_account,
            "all_transactions": [
                {
                    "id": str(t.id),
                    "transaction_type": t.transaction_type,
                    "account_type": t.account_type,
                    "amount": t.amount,
                    "status": t.status,
                    "description": t.description,
                    "goal_name": t.goal_name,
                    "created_at": t.created_at,
                    "reference": t.reference
                }
                for t in transactions
            ]
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": len(transactions) == limit
        }
    }

@router.get("/goals-progress", response_model=Dict[str, Any])
def get_goals_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed goals progress summary with:
    - Progress percentages
    - Time remaining
    - Projected completion
    - Savings rate analysis
    """
    
    safelocks = db.query(SafeLockAccount).filter(SafeLockAccount.user_id == current_user.id).all()
    mygoals = db.query(MyGoalAccount).filter(MyGoalAccount.user_id == current_user.id).all()
    
    all_goals = []
    total_progress = 0
    total_goals = 0
    
    # Process SafeLock goals
    for sl in safelocks:
        progress = (sl.current_amount / sl.target_amount * 100) if sl.target_amount > 0 else 0
        days_remaining = (sl.target_date - datetime.now().date()).days if sl.target_date else None
        
        # Calculate required daily savings
        remaining_amount = sl.target_amount - sl.current_amount
        required_daily = remaining_amount / days_remaining if days_remaining and days_remaining > 0 else 0
        
        goal_data = {
            "id": str(sl.id),
            "name": sl.goal_name,
            "type": "safelock",
            "target_amount": sl.target_amount,
            "current_amount": sl.current_amount,
            "progress_percentage": round(progress, 2),
            "days_remaining": days_remaining,
            "target_date": sl.target_date,
            "remaining_amount": remaining_amount,
            "required_daily_savings": round(required_daily, 2),
            "has_emergency_fund": sl.has_emergency_fund,
            "emergency_fund_percentage": sl.emergency_fund_percentage,
            "status": "on_track" if days_remaining and required_daily <= (sl.current_amount / max(days_remaining, 1)) else "needs_attention"
        }
        
        all_goals.append(goal_data)
        total_progress += progress
        total_goals += 1
    
    # Process MyGoal goals
    for mg in mygoals:
        progress = (mg.current_amount / mg.target_amount * 100) if mg.target_amount > 0 else 0
        days_remaining = (mg.target_date - datetime.now().date()).days if mg.target_date else None
        
        remaining_amount = mg.target_amount - mg.current_amount
        required_daily = remaining_amount / days_remaining if days_remaining and days_remaining > 0 else 0
        
        goal_data = {
            "id": str(mg.id),
            "name": mg.goal_name,
            "type": "mygoal",
            "target_amount": mg.target_amount,
            "current_amount": mg.current_amount,
            "progress_percentage": round(progress, 2),
            "days_remaining": days_remaining,
            "target_date": mg.target_date,
            "remaining_amount": remaining_amount,
            "required_daily_savings": round(required_daily, 2),
            "status": "on_track" if days_remaining and required_daily <= (mg.current_amount / max(days_remaining, 1)) else "needs_attention"
        }
        
        all_goals.append(goal_data)
        total_progress += progress
        total_goals += 1
    
    average_progress = total_progress / total_goals if total_goals > 0 else 0
    
    return {
        "goals": all_goals,
        "summary": {
            "total_goals": total_goals,
            "average_progress": round(average_progress, 2),
            "goals_on_track": len([g for g in all_goals if g["status"] == "on_track"]),
            "goals_needing_attention": len([g for g in all_goals if g["status"] == "needs_attention"]),
            "completed_goals": len([g for g in all_goals if g["progress_percentage"] >= 100])
        }
    }

def get_current_balances(user_id: UUID, db: Session) -> Dict[str, float]:
    """Helper function to get current account balances"""
    
    safelock_balance = (
        db.query(func.sum(SafeLockAccount.current_amount))
        .filter(SafeLockAccount.user_id == user_id)
        .scalar() or 0.0
    )
    
    mygoal_balance = (
        db.query(func.sum(MyGoalAccount.current_amount))
        .filter(MyGoalAccount.user_id == user_id)
        .scalar() or 0.0
    )
    
    emergency_fund = db.query(EmergencyFund).filter(EmergencyFund.user_id == user_id).first()
    emergency_balance = emergency_fund.balance if emergency_fund else 0.0
    
    flexi_account = db.query(FlexiAccount).filter(FlexiAccount.user_id == user_id).first()
    flexi_balance = flexi_account.balance if flexi_account else 0.0
    
    return {
        "total_balance": safelock_balance + mygoal_balance + emergency_balance + flexi_balance,
        "safelock_balance": safelock_balance,
        "mygoal_balance": mygoal_balance,
        "emergency_balance": emergency_balance,
        "flexi_balance": flexi_balance
    }
