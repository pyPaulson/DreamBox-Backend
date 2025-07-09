from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date
from typing import Literal 
from pydantic_core.core_schema import ValidationInfo 


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    gender: Literal["Male", "Female", "Other"]
    date_of_birth: date
    phone_number: str
    email: EmailStr
    password: str
    confirm_password: str
    agree_terms: bool 

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, confirm_password: str, info: ValidationInfo):
        password = info.data.get("password")  # ✅ this is correct now
        if password and confirm_password != password:
            raise ValueError("Passwords do not match")
        return confirm_password

    @field_validator("agree_terms")
    @classmethod
    def must_agree_terms(cls, value: bool):
        if not value:
            raise ValueError("You must agree to the terms and conditions")
        return value 
    

class LoginRequest(BaseModel):
    email: str
    password: str


class EmailVerificationInput(BaseModel):
    email: EmailStr
    code: str

class ResendCodeInput(BaseModel):
    email: EmailStr