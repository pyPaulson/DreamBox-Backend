from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import Date
from app.core.database import Base
import enum 

class Gender(str, enum.Enum):
       male = "Male"
       female = "Female"
       other = "Other"


class User(Base):
       __tablename__ = "users"

       id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
       first_name = Column(String, nullable=False)
       last_name = Column(String, nullable=False)
       gender = Column(SQLEnum(Gender), nullable=False)
       date_of_birth = Column(Date, nullable=False)
       phone_number = Column(String, unique=True, nullable=False)
       email = Column(String, unique=True, nullable=False)
       hashed_password = Column(String, nullable=False)
       is_phone_verified = Column(Boolean, default=False)
       email_verification_code = Column(String, nullable=True)
       email_code_expiry = Column(DateTime, nullable=True)
       is_verified = Column(Boolean, default=False)
       created_at = Column(DateTime, default=datetime.now(timezone.utc)) 
       pin = Column(String, nullable=True)