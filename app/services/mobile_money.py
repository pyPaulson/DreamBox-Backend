import httpx
import asyncio
from typing import Dict, Any, Optional
from enum import Enum
from app.models.wallets import WalletProvider
import logging
import os

logger = logging.getLogger(__name__)


class PaymentStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class PaymentError(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_WALLET = "invalid_wallet"
    NETWORK_ERROR = "network_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INVALID_AMOUNT = "invalid_amount"
    WALLET_NOT_FOUND = "wallet_not_found"
    PAYSTACK_ERROR = "paystack_error"


class PaystackService:
    """Service for handling payments through Paystack API"""
    
    def __init__(self):
        # Load Paystack configuration from environment variables
        self.secret_key = os.getenv("PAYSTACK_SECRET_KEY", "sk_test_your_paystack_secret_key")
        self.public_key = os.getenv("PAYSTACK_PUBLIC_KEY", "pk_test_your_paystack_public_key")
        self.base_url = "https://api.paystack.co"
        
        # Paystack supports multiple payment methods
        self.supported_providers = {
            WalletProvider.MTN: "mobile_money",
            WalletProvider.TELECEL: "mobile_money", 
            WalletProvider.AIRTELTIGO: "mobile_money"
        }
    
    async def process_payment(
        self, 
        provider: WalletProvider, 
        phone_number: str, 
        amount: float, 
        reference: str,
        description: str = "Auto-save deposit"
    ) -> Dict[str, Any]:
        """
        Process a payment through Paystack API
        
        Args:
            provider: Mobile money provider (MTN, Telecel, AirtelTigo)
            phone_number: Recipient phone number
            amount: Amount to transfer
            reference: Unique transaction reference
            description: Payment description
            
        Returns:
            Dict containing payment result with status, message, and transaction_id
        """
        try:
            return await self._process_paystack_payment(provider, phone_number, amount, reference, description)
                
        except Exception as e:
            logger.error(f"Paystack payment processing error: {str(e)}")
            return {
                "status": PaymentStatus.FAILED,
                "error": PaymentError.NETWORK_ERROR,
                "message": "Payment processing failed due to network error"
            }
    
    async def _process_paystack_payment(
        self, 
        provider: WalletProvider,
        phone_number: str, 
        amount: float, 
        reference: str, 
        description: str
    ) -> Dict[str, Any]:
        """Process payment through Paystack API"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json"
                }
                
                # Convert amount to kobo (Paystack uses kobo for GHS)
                amount_in_kobo = int(amount * 100)
                
                # Map provider to Paystack channel
                channel = self.supported_providers.get(provider, "mobile_money")
                
                payload = {
                    "amount": amount_in_kobo,
                    "currency": "GHS",
                    "reference": reference,
                    "description": description,
                    "customer": {
                        "phone": phone_number
                    },
                    "metadata": {
                        "provider": provider.value,
                        "auto_save": True,
                        "description": f"Auto-save deposit - {reference}"
                    },
                    "channels": [channel]
                }
                
                response = await client.post(
                    f"{self.base_url}/transaction/initialize",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status"):
                        return {
                            "status": PaymentStatus.SUCCESS,
                            "transaction_id": data.get("data", {}).get("reference"),
                            "access_code": data.get("data", {}).get("access_code"),
                            "authorization_url": data.get("data", {}).get("authorization_url"),
                            "message": "Payment initialized successfully"
                        }
                    else:
                        return {
                            "status": PaymentStatus.FAILED,
                            "error": PaymentError.PAYSTACK_ERROR,
                            "message": data.get("message", "Payment initialization failed")
                        }
                else:
                    error_data = response.json() if response.content else {}
                    error_message = error_data.get("message", "Payment failed")
                    
                    return {
                        "status": PaymentStatus.FAILED,
                        "error": PaymentError.PAYSTACK_ERROR,
                        "message": f"Paystack error: {error_message}"
                    }
                        
        except httpx.TimeoutException:
            return {
                "status": PaymentStatus.FAILED,
                "error": PaymentError.NETWORK_ERROR,
                "message": "Paystack service timeout"
            }
        except Exception as e:
            logger.error(f"Paystack payment error: {str(e)}")
            return {
                "status": PaymentStatus.FAILED,
                "error": PaymentError.NETWORK_ERROR,
                "message": "Paystack payment processing failed"
            }
    
    async def verify_payment(self, reference: str) -> Dict[str, Any]:
        """Verify payment status with Paystack"""
        try:
            async with httpx.AsyncClient() as client:
                headers = {
                    "Authorization": f"Bearer {self.secret_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.get(
                    f"{self.base_url}/transaction/verify/{reference}",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") and data.get("data", {}).get("status") == "success":
                        return {
                            "status": PaymentStatus.SUCCESS,
                            "transaction_id": data.get("data", {}).get("reference"),
                            "amount": data.get("data", {}).get("amount", 0) / 100,  # Convert from kobo
                            "message": "Payment verified successfully"
                        }
                    else:
                        return {
                            "status": PaymentStatus.FAILED,
                            "error": PaymentError.PAYSTACK_ERROR,
                            "message": "Payment verification failed"
                        }
                else:
                    return {
                        "status": PaymentStatus.FAILED,
                        "error": PaymentError.PAYSTACK_ERROR,
                        "message": "Payment verification failed"
                    }
                        
        except Exception as e:
            logger.error(f"Paystack verification error: {str(e)}")
            return {
                "status": PaymentStatus.FAILED,
                "error": PaymentError.NETWORK_ERROR,
                "message": "Payment verification failed"
            }


# Global instance
paystack_service = PaystackService()
