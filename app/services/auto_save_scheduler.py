import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.database import SessionLocal
from app.models.auto_save import AutoSaveSetting, AutoSaveTransaction, AutoSaveTransactionStatus
from app.models.goals import SafeLockAccount
from app.models.wallets import Wallet
from app.models.transactions import Transaction, TransactionType, AccountType, TransactionStatus
from app.services.mobile_money import paystack_service
from app.services.notification_service import auto_save_notification_service
from app.utils.transactions import generate_transaction_reference
import uuid

logger = logging.getLogger(__name__)


class AutoSaveScheduler:
    """Background service for processing auto-save executions"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 3600  # Check every hour (3600 seconds)
    
    async def start(self):
        """Start the auto-save scheduler"""
        if self.is_running:
            logger.warning("Auto-save scheduler is already running")
            return
        
        self.is_running = True
        logger.info("Auto-save scheduler started")
        
        while self.is_running:
            try:
                await self.process_auto_saves()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in auto-save scheduler: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop(self):
        """Stop the auto-save scheduler"""
        self.is_running = False
        logger.info("Auto-save scheduler stopped")
    
    async def process_auto_saves(self):
        """Process all due auto-save executions"""
        db = SessionLocal()
        try:
            # Find all active auto-save settings that are due for execution
            due_auto_saves = (
                db.query(AutoSaveSetting)
                .filter(
                    and_(
                        AutoSaveSetting.is_active == True,
                        AutoSaveSetting.next_execution <= datetime.now()
                    )
                )
                .all()
            )
            
            logger.info(f"Found {len(due_auto_saves)} auto-save settings due for execution")
            
            for auto_save in due_auto_saves:
                await self.process_single_auto_save(db, auto_save)
                
        except Exception as e:
            logger.error(f"Error processing auto-saves: {str(e)}")
            db.rollback()
        finally:
            db.close()
    
    async def process_single_auto_save(self, db: Session, auto_save: AutoSaveSetting):
        """Process a single auto-save execution"""
        try:
            # Get the goal and wallet - handle both SafeLock and MyGoal
            goal = None
            if auto_save.goal_type == 'safelock':
                goal = db.query(SafeLockAccount).filter(SafeLockAccount.id == auto_save.goal_id).first()
            elif auto_save.goal_type == 'mygoal':
                from app.models.goals import MyGoalAccount
                goal = db.query(MyGoalAccount).filter(MyGoalAccount.id == auto_save.goal_id).first()
            
            wallet = db.query(Wallet).filter(Wallet.id == auto_save.wallet_id).first()
            
            if not goal or not wallet:
                logger.error(f"Goal or wallet not found for auto-save {auto_save.id}")
                await self._record_failed_transaction(
                    db, auto_save, "Goal or wallet not found"
                )
                return
            
            # Check if goal is still active (not completed)
            if goal.current_amount >= goal.target_amount:
                logger.info(f"Goal {goal.id} is completed, disabling auto-save")
                auto_save.is_active = False
                db.commit()
                return
            
            # Create auto-save transaction record
            auto_save_transaction = AutoSaveTransaction(
                auto_save_id=auto_save.id,
                goal_id=auto_save.goal_id,
                amount=auto_save.amount,
                status=AutoSaveTransactionStatus.PENDING
            )
            db.add(auto_save_transaction)
            db.commit()
            db.refresh(auto_save_transaction)
            
            # Generate transaction reference
            reference = generate_transaction_reference()
            
            # Process payment through Paystack
            payment_result = await paystack_service.process_payment(
                provider=wallet.provider,
                phone_number=wallet.phone_number,
                amount=float(auto_save.amount),
                reference=reference,
                description=f"Auto-save deposit to {goal.goal_name}"
            )
            
            if payment_result["status"] == "success":
                await self._handle_successful_payment(
                    db, auto_save, auto_save_transaction, goal, reference, payment_result
                )
            else:
                await self._handle_failed_payment(
                    db, auto_save, auto_save_transaction, payment_result
                )
                
        except Exception as e:
            logger.error(f"Error processing auto-save {auto_save.id}: {str(e)}")
            await self._record_failed_transaction(db, auto_save, str(e))
    
    async def _handle_successful_payment(
        self, 
        db: Session, 
        auto_save: AutoSaveSetting, 
        auto_save_transaction: AutoSaveTransaction,
        goal: SafeLockAccount,
        reference: str,
        payment_result: dict
    ):
        """Handle successful payment"""
        try:
            # Update auto-save transaction
            auto_save_transaction.status = AutoSaveTransactionStatus.SUCCESS
            auto_save_transaction.payment_reference = payment_result.get("transaction_id")
            
            # Calculate amounts for goal and emergency fund
            amount = float(auto_save.amount)
            emergency_fund_amount = 0.0
            main_goal_amount = amount
            
            if goal.has_emergency_fund and goal.emergency_fund_percentage:
                emergency_fund_amount = amount * (goal.emergency_fund_percentage / 100)
                main_goal_amount = amount - emergency_fund_amount
            
            # Update goal balance
            goal.current_amount += main_goal_amount
            
            # Create main transaction record
            account_type = AccountType.SAFELOCK if auto_save.goal_type == 'safelock' else AccountType.MYGOAL
            transaction = Transaction(
                user_id=auto_save.user_id,
                goal_id=auto_save.goal_id,
                transaction_type=TransactionType.DEPOSIT,
                account_type=account_type,
                amount=amount,
                reference=reference,
                status=TransactionStatus.SUCCESSFUL,
                description=f"Auto-save deposit to {goal.goal_name}",
                goal_name=goal.goal_name,
                emergency_fund_amount=emergency_fund_amount,
                main_goal_amount=main_goal_amount,
                completed_at=datetime.now()
            )
            db.add(transaction)
            
            # Update emergency fund if applicable
            if emergency_fund_amount > 0:
                from app.models.goals import EmergencyFund
                emergency_fund = (
                    db.query(EmergencyFund)
                    .filter(EmergencyFund.user_id == auto_save.user_id)
                    .first()
                )
                if emergency_fund:
                    emergency_fund.balance += emergency_fund_amount
            
            # Calculate next execution time
            auto_save.next_execution = self._calculate_next_execution(
                auto_save.frequency, auto_save.time
            )
            
            db.commit()
            
            logger.info(f"Auto-save successful for goal {goal.id}, amount: {amount}")
            
            # Send success notification
            await auto_save_notification_service.send_success_notification(
                auto_save, goal, amount, wallet
            )
            
        except Exception as e:
            logger.error(f"Error handling successful payment: {str(e)}")
            db.rollback()
            raise
    
    async def _handle_failed_payment(
        self, 
        db: Session, 
        auto_save: AutoSaveSetting, 
        auto_save_transaction: AutoSaveTransaction,
        payment_result: dict
    ):
        """Handle failed payment"""
        try:
            # Get wallet for notification
            wallet = db.query(Wallet).filter(Wallet.id == auto_save.wallet_id).first()
            
            # Update auto-save transaction
            auto_save_transaction.status = AutoSaveTransactionStatus.FAILED
            auto_save_transaction.error_message = payment_result.get("message", "Payment failed")
            
            # Calculate next execution time (retry in 24 hours for failed payments)
            auto_save.next_execution = datetime.now() + timedelta(hours=24)
            
            db.commit()
            
            logger.warning(f"Auto-save failed for goal {auto_save.goal_id}: {payment_result.get('message')}")
            
            # Send failure notification
            if wallet:
                await auto_save_notification_service.send_failure_notification(
                    auto_save, payment_result.get("message", "Payment failed"), wallet
                )
            
        except Exception as e:
            logger.error(f"Error handling failed payment: {str(e)}")
            db.rollback()
            raise
    
    async def _record_failed_transaction(
        self, 
        db: Session, 
        auto_save: AutoSaveSetting, 
        error_message: str
    ):
        """Record a failed auto-save transaction"""
        try:
            auto_save_transaction = AutoSaveTransaction(
                auto_save_id=auto_save.id,
                goal_id=auto_save.goal_id,
                amount=auto_save.amount,
                status=AutoSaveTransactionStatus.FAILED,
                error_message=error_message
            )
            db.add(auto_save_transaction)
            
            # Set next execution to retry in 24 hours
            auto_save.next_execution = datetime.now() + timedelta(hours=24)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error recording failed transaction: {str(e)}")
            db.rollback()
    
    def _calculate_next_execution(self, frequency: str, time: datetime.time) -> datetime:
        """Calculate the next execution time"""
        now = datetime.now()
        today = now.date()
        
        # Create datetime for today with the specified time
        next_execution = datetime.combine(today, time)
        
        # If the time has already passed today, schedule for next occurrence
        if next_execution <= now:
            if frequency == "daily":
                next_execution += timedelta(days=1)
            elif frequency == "weekly":
                next_execution += timedelta(weeks=1)
            elif frequency == "monthly":
                # Add one month, handling month boundaries
                if next_execution.month == 12:
                    next_execution = next_execution.replace(year=next_execution.year + 1, month=1)
                else:
                    next_execution = next_execution.replace(month=next_execution.month + 1)
        
        return next_execution
    


# Global scheduler instance
auto_save_scheduler = AutoSaveScheduler()
