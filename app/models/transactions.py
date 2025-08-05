from sqlalchemy import Column, Float, String, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, timezone
from app.core.database import Base

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
