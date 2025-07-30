# schemas/safelock.py
from uuid import UUID
from pydantic import BaseModel, ValidationInfo, field_validator
from typing import Optional
from datetime import datetime


class SafeLockCreate(BaseModel):
    goal_name: str
    target_amount: float
    target_date: datetime
    has_emergency_fund: bool
    emergency_fund_percentage: Optional[int] = None
    agree_to_lock: bool

    @field_validator("emergency_fund_percentage")
    @classmethod
    def check_emergency_percentage(cls, value, info: ValidationInfo):
        has_emergency_fund = info.data.get("has_emergency_fund", False)

        if has_emergency_fund:
            if value is None:
                raise ValueError("Emergency fund percentage is required when emergency fund is enabled.")
            if not (0 <= value <= 30):
                raise ValueError("Emergency fund percentage must be between 0 and 30.")
        else:
            if value is not None:
                raise ValueError("Emergency fund percentage should not be provided when emergency fund is disabled.")
        return value
    
    @field_validator("agree_to_lock")
    @classmethod
    def must_agree_terms(cls, value: bool):
        if not value:
            raise ValueError("You must agree to the lock goal")
        return value 
    


class SafeLockResponse(BaseModel):
    id: UUID
    goal_name: str
    target_amount: float
    current_amount: float
    target_date: datetime
    has_emergency_fund: bool
    emergency_fund_percentage: Optional[int]
    created_at: datetime

    class Config:
        model_config = {
        "from_attributes": True  
    }
    

class MyGoalCreate(BaseModel):
    goal_name: str
    target_amount: float
    target_date: datetime


class MyGoalOut(BaseModel):
    id: UUID
    user_id: UUID
    goal_name: str
    target_amount: float
    current_amount: float
    target_date: datetime
    created_at: datetime

    model_config = {
        "from_attributes": True  
    }


class EmergencyFundOut(BaseModel):
    id: UUID
    user_id: UUID
    balance: float

    class Config:
        from_attributes = True


class FlexiAccountCreate(BaseModel):
    pass 


class FlexiAccountOut(BaseModel):
    id: UUID
    user_id: UUID
    balance: float

    class Config:
        from_attributes = True