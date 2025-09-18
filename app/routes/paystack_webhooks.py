from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.mobile_money import paystack_service
from app.models.auto_save import AutoSaveTransaction, AutoSaveTransactionStatus
from app.models.transactions import Transaction, TransactionStatus
from app.models.goals import SafeLockAccount, EmergencyFund
import hashlib
import hmac
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_paystack_signature(payload: str, signature: str) -> bool:
    """Verify Paystack webhook signature"""
    secret_key = os.getenv("PAYSTACK_SECRET_KEY", "")
    if not secret_key:
        logger.warning("Paystack secret key not configured")
        return False
    
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


@router.post("/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Paystack webhook events"""
    try:
        # Get the raw body and signature
        body = await request.body()
        signature = request.headers.get("x-paystack-signature", "")
        
        # Verify signature
        if not verify_paystack_signature(body.decode('utf-8'), signature):
            logger.warning("Invalid Paystack webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse the webhook data
        webhook_data = await request.json()
        event_type = webhook_data.get("event")
        data = webhook_data.get("data", {})
        
        logger.info(f"Received Paystack webhook: {event_type}")
        
        if event_type == "charge.success":
            await handle_successful_payment(db, data)
        elif event_type == "charge.failed":
            await handle_failed_payment(db, data)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing Paystack webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_successful_payment(db: Session, data: dict):
    """Handle successful payment from Paystack webhook"""
    try:
        reference = data.get("reference")
        amount = data.get("amount", 0) / 100  # Convert from kobo
        metadata = data.get("metadata", {})
        
        # Check if this is an auto-save transaction
        if metadata.get("auto_save"):
            # Find the auto-save transaction
            auto_save_transaction = (
                db.query(AutoSaveTransaction)
                .filter(AutoSaveTransaction.payment_reference == reference)
                .first()
            )
            
            if auto_save_transaction:
                # Update auto-save transaction status
                auto_save_transaction.status = AutoSaveTransactionStatus.SUCCESS
                
                # Get the goal and update balance
                goal = (
                    db.query(SafeLockAccount)
                    .filter(SafeLockAccount.id == auto_save_transaction.goal_id)
                    .first()
                )
                
                if goal:
                    # Calculate amounts for goal and emergency fund
                    emergency_fund_amount = 0.0
                    main_goal_amount = amount
                    
                    if goal.has_emergency_fund and goal.emergency_fund_percentage:
                        emergency_fund_amount = amount * (goal.emergency_fund_percentage / 100)
                        main_goal_amount = amount - emergency_fund_amount
                    
                    # Update goal balance
                    goal.current_amount += main_goal_amount
                    
                    # Update emergency fund if applicable
                    if emergency_fund_amount > 0:
                        emergency_fund = (
                            db.query(EmergencyFund)
                            .filter(EmergencyFund.user_id == goal.user_id)
                            .first()
                        )
                        if emergency_fund:
                            emergency_fund.balance += emergency_fund_amount
                    
                    # Update main transaction record
                    transaction = (
                        db.query(Transaction)
                        .filter(Transaction.reference == reference)
                        .first()
                    )
                    
                    if transaction:
                        transaction.status = TransactionStatus.SUCCESSFUL
                        transaction.emergency_fund_amount = emergency_fund_amount
                        transaction.main_goal_amount = main_goal_amount
                    
                    db.commit()
                    logger.info(f"Successfully processed auto-save payment: {reference}")
                else:
                    logger.error(f"Goal not found for auto-save transaction: {reference}")
            else:
                logger.warning(f"Auto-save transaction not found for reference: {reference}")
        else:
            logger.info(f"Non-auto-save payment processed: {reference}")
            
    except Exception as e:
        logger.error(f"Error handling successful payment: {str(e)}")
        db.rollback()


async def handle_failed_payment(db: Session, data: dict):
    """Handle failed payment from Paystack webhook"""
    try:
        reference = data.get("reference")
        metadata = data.get("metadata", {})
        
        # Check if this is an auto-save transaction
        if metadata.get("auto_save"):
            # Find the auto-save transaction
            auto_save_transaction = (
                db.query(AutoSaveTransaction)
                .filter(AutoSaveTransaction.payment_reference == reference)
                .first()
            )
            
            if auto_save_transaction:
                # Update auto-save transaction status
                auto_save_transaction.status = AutoSaveTransactionStatus.FAILED
                auto_save_transaction.error_message = data.get("gateway_response", "Payment failed")
                
                # Update main transaction record
                transaction = (
                    db.query(Transaction)
                    .filter(Transaction.reference == reference)
                    .first()
                )
                
                if transaction:
                    transaction.status = TransactionStatus.FAILED
                
                db.commit()
                logger.info(f"Marked auto-save payment as failed: {reference}")
            else:
                logger.warning(f"Auto-save transaction not found for failed payment: {reference}")
        else:
            logger.info(f"Non-auto-save payment failed: {reference}")
            
    except Exception as e:
        logger.error(f"Error handling failed payment: {str(e)}")
        db.rollback()
