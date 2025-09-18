from uuid import UUID
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, time
from decimal import Decimal
from app.models.auto_save import AutoSaveFrequency, AutoSaveTransactionStatus


class AutoSaveCreate(BaseModel):
    wallet_id: UUID
    frequency: AutoSaveFrequency
    time: time
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal):
        if value <= 0:
            raise ValueError("Amount must be greater than 0")
        if value < 1.00:
            raise ValueError("Minimum amount is 1.00")
        if value > 10000.00:
            raise ValueError("Maximum amount is 10,000.00")
        return value

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: time):
        # Time validation is handled by Pydantic's time type
        return value


class AutoSaveUpdate(BaseModel):
    wallet_id: Optional[UUID] = None
    frequency: Optional[AutoSaveFrequency] = None
    time: Optional[time] = None
    amount: Optional[Decimal] = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Optional[Decimal]):
        if value is not None:
            if value <= 0:
                raise ValueError("Amount must be greater than 0")
            if value < 1.00:
                raise ValueError("Minimum amount is 1.00")
            if value > 10000.00:
                raise ValueError("Maximum amount is 10,000.00")
        return value


class AutoSaveResponse(BaseModel):
    id: UUID
    goal_id: UUID
    goal_type: str
    wallet_id: UUID
    frequency: AutoSaveFrequency
    time: time
    amount: Decimal
    is_active: bool
    next_execution: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutoSaveTransactionResponse(BaseModel):
    id: UUID
    goal_id: UUID
    goal_type: str
    amount: Decimal
    status: AutoSaveTransactionStatus
    payment_reference: Optional[str]
    error_message: Optional[str]
    executed_at: datetime

    class Config:
        from_attributes = True


class AutoSaveTransactionListResponse(BaseModel):
    transactions: list[AutoSaveTransactionResponse]
    total: int
    limit: int
    offset: int


class MessageResponse(BaseModel):
    message: str
