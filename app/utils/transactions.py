from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import logging

from app.models.transactions import Transaction, TransactionType, AccountType, TransactionStatus
from app.models.goals import SafeLockAccount, MyGoalAccount, EmergencyFund, FlexiAccount
from app.models.user import User
from app.schemas.transactions import (
    TransactionResponse, TransactionFilter, AccountStatement, 
    AccountSummary, TransactionSummary
)

logger = logging.getLogger(__name__)


def generate_transaction_reference() -> str:
    """Generate a unique transaction reference"""
    return f"AUTO_SAVE_{uuid4().hex[:12].upper()}"


class TransactionService:
    
    @staticmethod
    def create_transaction(
        db: Session,
        user_id: str,
        transaction_type: TransactionType,
        account_type: AccountType,
        amount: float,
        goal_id: Optional[str] = None,
        description: Optional[str] = None,
        reference: Optional[str] = None
    ) -> Transaction:
        """Create a new transaction record"""
        
        if not reference:
            reference = f"{transaction_type.value}_{uuid4().hex[:12]}"
        
        # Get goal name if applicable
        goal_name = None
        if goal_id:
            if account_type == AccountType.SAFELOCK:
                goal = db.query(SafeLockAccount).filter(SafeLockAccount.id == goal_id).first()
                goal_name = goal.goal_name if goal else None
            elif account_type == AccountType.MYGOAL:
                goal = db.query(MyGoalAccount).filter(MyGoalAccount.id == goal_id).first()
                goal_name = goal.goal_name if goal else None
        
        # Generate description if not provided
        if not description:
            if transaction_type == TransactionType.DEPOSIT:
                if goal_name:
                    description = f"Deposit to {goal_name} ({account_type.value})"
                else:
                    description = f"Deposit to {account_type.value} account"
            else:
                if goal_name:
                    description = f"Withdrawal from {goal_name} ({account_type.value})"
                else:
                    description = f"Withdrawal from {account_type.value} account"
        
        transaction = Transaction(
            user_id=user_id,
            goal_id=goal_id,
            transaction_type=transaction_type,
            account_type=account_type,
            amount=amount,
            reference=reference,
            description=description,
            goal_name=goal_name,
            status=TransactionStatus.PENDING
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Created transaction {transaction.id} for user {user_id}")
        return transaction
    
    @staticmethod
    def complete_transaction(
        db: Session,
        transaction_id: str,
        emergency_fund_amount: float = 0.0,
        main_goal_amount: Optional[float] = None
    ) -> Transaction:
        """Mark transaction as successful and update amounts"""
        
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            raise ValueError("Transaction not found")
        
        transaction.status = TransactionStatus.SUCCESSFUL
        transaction.completed_at = datetime.utcnow()
        transaction.emergency_fund_amount = emergency_fund_amount
        transaction.main_goal_amount = main_goal_amount
        
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Completed transaction {transaction.id}")
        return transaction
    
    @staticmethod
    def get_user_transactions(
        db: Session,
        user_id: str,
        filters: Optional[TransactionFilter] = None
    ) -> List[Transaction]:
        """Get user transactions with optional filters"""
        
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

         # Order by most recent first
        query = query.order_by(desc(Transaction.created_at))
        
        if filters:
            if filters.account_type:
                query = query.filter(Transaction.account_type == filters.account_type)
            
            if filters.transaction_type:
                query = query.filter(Transaction.transaction_type == filters.transaction_type)
            
            if filters.goal_id:
                query = query.filter(Transaction.goal_id == filters.goal_id)
            
            if filters.start_date:
                query = query.filter(Transaction.created_at >= filters.start_date)
            
            if filters.end_date:
                query = query.filter(Transaction.created_at <= filters.end_date)
            
            # Apply pagination
            query = query.offset(filters.offset or 0)
            query = query.limit(filters.limit or 50)
        

        logger.info(f"Filters received: {filters}")

        
        return query.all()
    
    @staticmethod
    def get_recent_transactions(
        db: Session,
        user_id: str,
        limit: int = 5
    ) -> List[Transaction]:
        """Get recent successful transactions for home screen"""
        
        return (
            db.query(Transaction)
            .filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.status == TransactionStatus.SUCCESSFUL
                )
            )
            .order_by(desc(Transaction.completed_at))
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_account_statement(
        db: Session,
        user_id: str,
        filters: Optional[TransactionFilter] = None
    ) -> AccountStatement:
        """Generate account statement with summary"""
        
        # Get all balances
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Calculate balances
        safelock_balance = sum([sl.current_amount for sl in user.safelocks])
        mygoal_balance = sum([mg.current_amount for mg in user.mygoals])
        emergency_balance = user.emergency_fund.balance if user.emergency_fund else 0.0
        flexi_balance = user.flexi_account.balance if user.flexi_account else 0.0
        
        total_balance = safelock_balance + mygoal_balance + emergency_balance + flexi_balance
        
        # Get filtered transactions
        transactions = TransactionService.get_user_transactions(db, user_id, filters)
        
        # Calculate totals for filtered transactions
        successful_transactions = [t for t in transactions if t.status == TransactionStatus.SUCCESSFUL]
        total_deposits = sum([t.amount for t in successful_transactions if t.transaction_type == TransactionType.DEPOSIT])
        total_withdrawals = sum([t.amount for t in successful_transactions if t.transaction_type == TransactionType.WITHDRAWAL])

        logger.info(f"User balances: safelocks={user.safelocks}, mygoals={user.mygoals}, emergency={user.emergency_fund}, flexi={user.flexi_account}")

        
        return AccountStatement(
            user_id=user_id,
            account_balance=total_balance,
            total_deposits=total_deposits,
            total_withdrawals=total_withdrawals,
            transaction_count=len(transactions),
            transactions=[TransactionResponse.model_validate(t) for t in transactions]
        )
    
    @staticmethod
    def get_transaction_summary(
        db: Session,
        user_id: str,
        days: int = 30
    ) -> TransactionSummary:
        """Get transaction summary for specified period"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        transactions = (
            db.query(Transaction)
            .filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.status == TransactionStatus.SUCCESSFUL,
                    Transaction.completed_at >= start_date
                )
            )
            .order_by(desc(Transaction.completed_at))
            .all()
        )
        
        total_deposits = sum([t.amount for t in transactions if t.transaction_type == TransactionType.DEPOSIT])
        total_withdrawals = sum([t.amount for t in transactions if t.transaction_type == TransactionType.WITHDRAWAL])
        
        return TransactionSummary(
            total_deposits=total_deposits,
            total_withdrawals=total_withdrawals,
            total_transactions=len(transactions),
            recent_transactions=[TransactionResponse.model_validate(t) for t in transactions[:10]]
        )