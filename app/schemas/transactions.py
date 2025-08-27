from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class AccountType(str, Enum):
    SAFELOCK = "safelock"
    MYGOAL = "mygoal"
    EMERGENCY = "emergency"
    FLEXI = "flexi"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"

class TransactionBase(BaseModel):
    transaction_type: TransactionType
    account_type: AccountType
    amount: float = Field(..., gt=0)
    goal_id: Optional[UUID] = None
    description: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    reference: str
    status: TransactionStatus
    goal_name: Optional[str] = None
    emergency_fund_amount: float = 0.0
    main_goal_amount: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TransactionSummary(BaseModel):
    total_deposits: float = 0.0
    total_withdrawals: float = 0.0
    total_transactions: int = 0
    recent_transactions: List[TransactionResponse] = []

class TransactionFilter(BaseModel):
    account_type: Optional[AccountType] = None
    transaction_type: Optional[TransactionType] = None
    goal_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = Field(default=50, le=100)
    offset: Optional[int] = Field(default=0, ge=0)

class AccountStatement(BaseModel):
    user_id: UUID
    account_balance: float
    total_deposits: float
    total_withdrawals: float
    transaction_count: int
    transactions: List[TransactionResponse]
    
class AccountSummary(BaseModel):
    total_balance: float
    safelock_balance: float
    mygoal_balance: float
    emergency_balance: float
    flexi_balance: float
    recent_transactions: List[TransactionResponse]