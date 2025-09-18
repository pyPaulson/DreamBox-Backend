from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timezone
from app.core.database import Base
import enum


class WalletProvider(str, enum.Enum):
    MTN = "MTN"
    TELECEL = "Telecel"
    AIRTELTIGO = "AirtelTigo"


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(SQLEnum(WalletProvider), nullable=False)
    phone_number = Column(String(15), nullable=False)
    account_name = Column(String(100), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="wallets")
    auto_save_settings = relationship("AutoSaveSetting", back_populates="wallet")

    # Constraints
    __table_args__ = (
        CheckConstraint("provider IN ('MTN', 'Telecel', 'AirtelTigo')", name="check_wallet_provider"),
        # Unique constraint for user_id, phone_number, provider combination
        # This will be handled in the migration file
    )

    def __repr__(self):
        return f"<Wallet {self.provider} {self.phone_number}>"
