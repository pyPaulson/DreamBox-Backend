from datetime import datetime, timedelta
import random
import smtplib
from email.message import EmailMessage
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, get_db
from app.core.jwt import create_access_token
from app.dependencies.auth import get_current_user
from app.schemas.user import EmailVerificationInput, LoginRequest, ResendCodeInput, SetPinInput, UserCreate, UserOut
from app.models.user import User
from app.core.security import hash_password, hash_pin, verify_password, verify_pin
import os
from dotenv import load_dotenv

load_dotenv()

email_host = os.getenv("EMAIL_HOST")            
email_port = int(os.getenv("EMAIL_PORT"))       
email_user = os.getenv("EMAIL_HOST_USER")            
email_pass = os.getenv("EMAIL_HOST_PASSWORD") 

router = APIRouter(tags=["Authentication"])

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("/register")
def register(user_data: UserCreate, db: db_dependency):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if db.query(User).filter(User.phone_number == user_data.phone_number).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    new_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        gender=user_data.gender,
        date_of_birth=user_data.date_of_birth,
        phone_number=user_data.phone_number,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully. Proceed to email verification.",
         "access_token": "xxx.jwt.token.here",
        "user_id": str(new_user.id),
        "first_name": new_user.first_name,
    }



@router.post("/send-verification-code")
def send_verification_code(email: str, db: db_dependency):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")

    code = ''.join(str(random.randint(0, 9)) for _ in range(6)) 
    expiry = datetime.now() + timedelta(minutes=10)  

    user.email_verification_code = code
    user.email_code_expiry = expiry
    db.commit()

    msg = EmailMessage()
    msg["Subject"] = "DreamBox Email Verification Code"
    msg["From"] = "agyekumpaul07@gmail.com"
    msg["To"] = user.email
    msg.set_content(f"""
    Hello {user.first_name},

    Your DreamBox 6-digit verification code is: {code}
    It will expire in 10 minutes.

    Thanks,
    DreamBox Team
    """)

    try:
        with smtplib.SMTP(email_host, email_port) as smtp:  
            smtp.starttls()
            smtp.login(email_user, email_pass)
            smtp.send_message(msg)
            print(f"Verification email sent to {user.email} ✅")
    except Exception as e:
        print("Failed to send email ❌", str(e))
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {
        "message": "Verification code sent successfully"
    }




@router.post("/verify-email")
def verify_email(
    data: EmailVerificationInput,
    db: db_dependency,
):
    
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Your email is already verified ✅"}

    if not user.email_verification_code:
        raise HTTPException(status_code=400, detail="No verification code sent to this email")

    if datetime.now() > user.email_code_expiry:
        raise HTTPException(status_code=400, detail="Verification code has expired")

    if data.code != user.email_verification_code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.is_verified = True
    user.email_verification_code = None
    user.email_code_expiry = None
    db.commit()

    return {"message": "Email verified successfully ✅."}


@router.post("/resend-code")
def resend_verification_code(data: ResendCodeInput, db: db_dependency):
    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        raise HTTPException(status_code=400, detail="User is already verified")

    code = ''.join(str(random.randint(0, 9)) for _ in range(6))
    expiry = datetime.now() + timedelta(minutes=10)

    user.email_verification_code = code
    user.email_code_expiry = expiry
    db.commit()

    msg = EmailMessage()
    msg["Subject"] = "DreamBox Email Verification Code"
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = user.email
    msg.set_content(
        f"Hello {user.first_name},\n\n"
        f"Your verification code is: {code}\n"
        f"This code expires in 10 minutes.\n\n"
        f"Thanks,\nDreamBox Team"
    )

    try:
        with smtplib.SMTP(os.getenv("EMAIL_HOST"), email_port) as smtp:
            smtp.starttls()
            smtp.login(os.getenv("EMAIL_HOST_USER"), os.getenv("EMAIL_HOST_PASSWORD"))
            smtp.send_message(msg)
    except Exception as e:
        print("❌ Failed to resend email:", e)
        raise HTTPException(status_code=500, detail="Could not send email")

    return {"message": "Verification code resent successfully ✅"}



@router.post("/login")
def login(user_data: LoginRequest, db: db_dependency):
    user = db.query(User).filter(
        (User.email == user_data.email)
        ).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": str(user.id)})

    return {
    "access_token": token,
    "token_type": "bearer",
    "first_name": user.first_name,
}

@router.post("/set-pin")
def set_user_pin(data: SetPinInput, db: db_dependency):
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.pin:
        raise HTTPException(status_code=400, detail="PIN already set")

    user.pin = hash_password(data.pin)
    db.commit()

    return {"message": "PIN set successfully"}


@router.post("/verify-pin")
def verify_user_pin(data: SetPinInput, db: db_dependency, current_user: User = Depends(get_current_user)):
    if not current_user.transaction_pin:
        raise HTTPException(status_code=400, detail="No PIN set.")

    if not verify_pin(data.pin, current_user.transaction_pin):
        raise HTTPException(status_code=401, detail="Incorrect PIN")

    return {"message": "PIN verified successfully."}




@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "date_of_birth": current_user.date_of_birth,
    }


