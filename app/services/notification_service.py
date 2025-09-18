"""
Notification service for auto-save events
This integrates with the existing notification system to send auto-save notifications
"""

import logging
from typing import Dict, Any
from datetime import datetime
from app.models.auto_save import AutoSaveSetting
from app.models.goals import SafeLockAccount
from app.models.wallets import Wallet

logger = logging.getLogger(__name__)


class AutoSaveNotificationService:
    """Service for sending auto-save related notifications"""
    
    def __init__(self):
        self.notification_queue = []  # In production, use Redis or message queue
    
    async def send_success_notification(
        self, 
        auto_save: AutoSaveSetting, 
        goal: SafeLockAccount, 
        amount: float,
        wallet: Wallet
    ):
        """Send success notification for auto-save"""
        try:
            notification_data = {
                "user_id": str(auto_save.user_id),
                "type": "auto_save_success",
                "title": "Auto-Save Successful! 🎉",
                "message": f"GHS {amount:.2f} has been automatically added to your {goal.goal_name} goal.",
                "data": {
                    "goal_id": str(goal.id),
                    "amount": amount,
                    "goal_name": goal.goal_name,
                    "wallet_provider": wallet.provider.value,
                    "auto_save_id": str(auto_save.id)
                },
                "created_at": datetime.now().isoformat()
            }
            
            # Add to notification queue
            self.notification_queue.append(notification_data)
            
            # TODO: Integrate with your existing notification system
            # This could be:
            # 1. Store in database for in-app notifications
            # 2. Send push notification via FCM/APNs
            # 3. Send email notification
            # 4. Send SMS notification
            
            logger.info(f"Success notification queued for user {auto_save.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending success notification: {str(e)}")
    
    async def send_failure_notification(
        self, 
        auto_save: AutoSaveSetting, 
        error_message: str,
        wallet: Wallet
    ):
        """Send failure notification for auto-save"""
        try:
            # Determine user-friendly error message
            user_message = self._get_user_friendly_error_message(error_message, wallet.provider.value)
            
            notification_data = {
                "user_id": str(auto_save.user_id),
                "type": "auto_save_failed",
                "title": "Auto-Save Failed",
                "message": user_message,
                "data": {
                    "goal_id": str(auto_save.goal_id),
                    "error": self._get_error_type(error_message),
                    "wallet_provider": wallet.provider.value,
                    "auto_save_id": str(auto_save.id),
                    "retry_time": "24 hours"
                },
                "created_at": datetime.now().isoformat()
            }
            
            # Add to notification queue
            self.notification_queue.append(notification_data)
            
            # TODO: Integrate with your existing notification system
            
            logger.info(f"Failure notification queued for user {auto_save.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending failure notification: {str(e)}")
    
    def _get_user_friendly_error_message(self, error_message: str, provider: str) -> str:
        """Convert technical error messages to user-friendly messages"""
        error_lower = error_message.lower()
        
        if "insufficient" in error_lower:
            return f"Auto-save failed: Insufficient funds in your {provider} wallet. Please add funds and try again."
        elif "invalid" in error_lower or "not found" in error_lower:
            return f"Auto-save failed: Invalid {provider} wallet number. Please update your wallet details."
        elif "network" in error_lower or "timeout" in error_lower:
            return f"Auto-save failed: Network issue with {provider} service. We'll retry in 24 hours."
        elif "service" in error_lower or "unavailable" in error_lower:
            return f"Auto-save failed: {provider} service is temporarily unavailable. We'll retry in 24 hours."
        else:
            return f"Auto-save failed: {error_message}. We'll retry in 24 hours."
    
    def _get_error_type(self, error_message: str) -> str:
        """Determine error type from error message"""
        error_lower = error_message.lower()
        
        if "insufficient" in error_lower:
            return "insufficient_funds"
        elif "invalid" in error_lower or "not found" in error_lower:
            return "invalid_wallet"
        elif "network" in error_lower or "timeout" in error_lower:
            return "network_error"
        elif "service" in error_lower or "unavailable" in error_lower:
            return "service_unavailable"
        else:
            return "unknown_error"
    
    async def send_auto_save_disabled_notification(
        self, 
        auto_save: AutoSaveSetting, 
        reason: str
    ):
        """Send notification when auto-save is disabled"""
        try:
            notification_data = {
                "user_id": str(auto_save.user_id),
                "type": "auto_save_disabled",
                "title": "Auto-Save Disabled",
                "message": f"Auto-save has been disabled for your goal. Reason: {reason}",
                "data": {
                    "goal_id": str(auto_save.goal_id),
                    "reason": reason,
                    "auto_save_id": str(auto_save.id)
                },
                "created_at": datetime.now().isoformat()
            }
            
            # Add to notification queue
            self.notification_queue.append(notification_data)
            
            logger.info(f"Auto-save disabled notification queued for user {auto_save.user_id}")
            
        except Exception as e:
            logger.error(f"Error sending auto-save disabled notification: {str(e)}")
    
    def get_notification_queue(self) -> list:
        """Get all queued notifications (for testing/debugging)"""
        return self.notification_queue.copy()
    
    def clear_notification_queue(self):
        """Clear the notification queue (for testing/debugging)"""
        self.notification_queue.clear()


# Global notification service instance
auto_save_notification_service = AutoSaveNotificationService()
