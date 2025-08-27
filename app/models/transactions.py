from sqlalchemy import Column, Float, String, ForeignKey, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, timezone
from app.core.database import Base
import enum

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class AccountType(str, enum.Enum):
    SAFELOCK = "safelock"
    MYGOAL = "mygoal" 
    EMERGENCY = "emergency"
    FLEXI = "flexi"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), nullable=True)  # For safelock/mygoal transactions
    
    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    amount = Column(Float, nullable=False)
    
    # Payment details
    reference = Column(String, unique=True, nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Description and metadata
    description = Column(Text, nullable=True)
    goal_name = Column(String, nullable=True)  # Store goal name for display
    
    # Emergency fund split (for safelock with emergency fund)
    emergency_fund_amount = Column(Float, default=0.0)
    main_goal_amount = Column(Float, nullable=True)  # Amount that went to main goal
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_type} {self.amount} for {self.account_type}>"

# Update the DepositTransaction to be simpler (or remove if replacing with Transaction)
class DepositTransaction(Base):
    __tablename__ = "deposit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    goal_id = Column(UUID(as_uuid=True), nullable=True)
    amount = Column(Float, nullable=False)
    reference = Column(String, unique=True, nullable=False)
    account_type = Column(String, nullable=False)  
    is_successful = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="deposits")

class WithdrawalTransaction(Base):
    __tablename__ = "withdrawal_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), nullable=True)
    
    amount = Column(Float, nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    reference = Column(String, unique=True, nullable=False)
    
    # Withdrawal specific fields
    reason = Column(Text, nullable=True)  # For emergency withdrawals
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    
    # Banking details for withdrawal
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    account_name = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="withdrawals")