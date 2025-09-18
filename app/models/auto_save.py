from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint, Time, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timezone
from app.core.database import Base
import enum


class AutoSaveFrequency(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AutoSaveTransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutoSaveSetting(Base):
    __tablename__ = "auto_save_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    goal_id = Column(UUID(as_uuid=True), nullable=False)  # Can reference either SafeLock or MyGoal
    goal_type = Column(String(20), nullable=False, default='safelock')  # 'safelock' or 'mygoal'
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    frequency = Column(SQLEnum(AutoSaveFrequency), nullable=False)
    time = Column(Time, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    next_execution = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="auto_save_settings")
    wallet = relationship("Wallet", back_populates="auto_save_settings")
    # Note: goal relationship removed since goal_id can reference different tables
    transactions = relationship("AutoSaveTransaction", back_populates="auto_save_setting")

    # Constraints
    __table_args__ = (
        CheckConstraint("frequency IN ('daily', 'weekly', 'monthly')", name="check_auto_save_frequency"),
        CheckConstraint("amount > 0", name="check_auto_save_amount_positive"),
        # Unique constraint for one auto-save setting per goal
        # This will be handled in the migration file
    )

    def __repr__(self):
        return f"<AutoSaveSetting {self.frequency} {self.amount} for goal {self.goal_id}>"


class AutoSaveTransaction(Base):
    __tablename__ = "auto_save_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    auto_save_id = Column(UUID(as_uuid=True), ForeignKey("auto_save_settings.id", ondelete="CASCADE"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), nullable=False)  # Can reference either SafeLock or MyGoal
    goal_type = Column(String(20), nullable=False, default='safelock')  # 'safelock' or 'mygoal'
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLEnum(AutoSaveTransactionStatus), nullable=False)
    payment_reference = Column(String(100), nullable=True)
    error_message = Column(String, nullable=True)
    executed_at = Column(DateTime, default=datetime.now(timezone.utc))
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    auto_save_setting = relationship("AutoSaveSetting", back_populates="transactions")
    # Note: goal relationship removed since goal_id can reference different tables

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'success', 'failed', 'cancelled')", name="check_auto_save_transaction_status"),
    )

    def __repr__(self):
        return f"<AutoSaveTransaction {self.amount} {self.status}>"
