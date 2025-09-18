from uuid import UUID
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
from app.models.wallets import WalletProvider


class WalletCreate(BaseModel):
    provider: WalletProvider
    phone_number: str
    account_name: str
    is_default: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str):
        # Ghanaian phone number validation
        if not value:
            raise ValueError("Phone number is required")
        
        # Remove any spaces or dashes
        cleaned = value.replace(" ", "").replace("-", "")
        
        # Check if it starts with 0 and has 10 digits total
        if not (cleaned.startswith("0") and len(cleaned) == 10 and cleaned[1:].isdigit()):
            raise ValueError("Phone number must be in Ghanaian format (e.g., 0241234567)")
        
        # Check if it's a valid Ghanaian mobile number
        valid_prefixes = ["024", "020", "027", "055", "059", "054", "056", "057"]
        if not any(cleaned.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError("Invalid Ghanaian mobile number prefix")
        
        return cleaned

    @field_validator("account_name")
    @classmethod
    def validate_account_name(cls, value: str):
        if not value or len(value.strip()) < 2:
            raise ValueError("Account name must be at least 2 characters long")
        return value.strip()


class WalletUpdate(BaseModel):
    provider: Optional[WalletProvider] = None
    phone_number: Optional[str] = None
    account_name: Optional[str] = None
    is_default: Optional[bool] = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: Optional[str]):
        if value is not None:
            # Remove any spaces or dashes
            cleaned = value.replace(" ", "").replace("-", "")
            
            # Check if it starts with 0 and has 10 digits total
            if not (cleaned.startswith("0") and len(cleaned) == 10 and cleaned[1:].isdigit()):
                raise ValueError("Phone number must be in Ghanaian format (e.g., 0241234567)")
            
            # Check if it's a valid Ghanaian mobile number
            valid_prefixes = ["024", "020", "027", "055", "059", "054", "056", "057"]
            if not any(cleaned.startswith(prefix) for prefix in valid_prefixes):
                raise ValueError("Invalid Ghanaian mobile number prefix")
            
            return cleaned
        return value

    @field_validator("account_name")
    @classmethod
    def validate_account_name(cls, value: Optional[str]):
        if value is not None:
            if len(value.strip()) < 2:
                raise ValueError("Account name must be at least 2 characters long")
            return value.strip()
        return value


class WalletResponse(BaseModel):
    id: UUID
    provider: WalletProvider
    phone_number: str
    account_name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletListResponse(BaseModel):
    wallets: list[WalletResponse]


class MessageResponse(BaseModel):
    message: str
