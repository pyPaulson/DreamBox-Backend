from uuid import uuid4
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.core.database import Base


class SafeLockAccount(Base):
    __tablename__ = "safeLock_account"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    goal_name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, nullable=False, default=0.0)
    target_date = Column(Date, nullable=False)
    has_emergency_fund = Column(Boolean, default=False)
    emergency_fund_percentage = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="safelocks")



class MyGoalAccount(Base):
    __tablename__ = "myGoal_account"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    goal_name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, nullable=False, default=0.0)
    target_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    user = relationship("User", back_populates="mygoals")


class EmergencyFund(Base):
    __tablename__ = "emergency_funds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    balance = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0) 

    user = relationship("User", back_populates="emergency_fund")


class FlexiAccount(Base):
    __tablename__ = "flexi_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    balance = Column(Float, default=0.0)

    user = relationship("User", back_populates="flexi_account")