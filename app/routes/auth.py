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
from app.schemas.user import EmailVerificationInput, LoginRequest, UserCreate
from app.models.user import User
from app.core.security import hash_password, verify_password
import os
from dotenv import load_dotenv

load_dotenv()

email_host = os.getenv("EMAIL_HOST")            
email_port = int(os.getenv("EMAIL_PORT"))       
email_user = os.getenv("EMAIL_HOST_USER")            
email_pass = os.getenv("EMAIL_HOST_PASSWORD") 

router = APIRouter()

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

db_dependency = Annotated[Session, Depends(get_db)]
@router.post("/register")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
   
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

 
    code = ''.join(str(random.randint(0, 9)) for _ in range(6))  # e.g. "123456"
    expiry = datetime.now() + timedelta(minutes=10)  # expires in 10 mins

    new_user.email_verification_code = code
    new_user.email_code_expiry = expiry

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    msg = EmailMessage()
    msg["Subject"] = "DreamBox Email Verification Code"
    msg["From"] = "agyekumpaul07@gmail.com" 
    msg["To"] = new_user.email
    msg.set_content(f"""
    Hello {new_user.first_name},

    Your DreamBox 6-digit verification code is: {code}
    It will expire in 10 minutes.

    Thanks,
    DreamBox Team
    """)

    try:
        with smtplib.SMTP(email_host, email_port) as smtp:  # Or use smtp.gmail.com
            smtp.starttls()
            smtp.login(email_user, email_pass)
            smtp.send_message(msg)
            print(f"Verification email sent to {new_user.email} ✅")
    except Exception as e:
        print("Failed to send email ❌", str(e))

    return {
        "message": "User registered successfully. A verification code has been sent to your email.",
        "user_id": str(new_user.id)
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

    # Step 2: Mark user as verified
    user.is_verified = True
    user.email_verification_code = None
    user.email_code_expiry = None
    db.commit()

    return {"message": "Email verified successfully ✅. You can now log in."}


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
    "user": {
        "id": str(user.id),
        "first_name": user.first_name
    }
}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
    }

