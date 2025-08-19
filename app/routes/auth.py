from datetime import datetime, timedelta
import random
import smtplib
from email.message import EmailMessage
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.jwt import create_access_token
from app.dependencies.auth import get_current_user
from app.schemas.user import EmailVerificationInput, LoginRequest, ResendCodeInput, SetPinInput, UserCreate, UserOut
from app.models.user import User
from app.core.security import hash_password, hash_pin, verify_password, verify_pin
import os
import shutil
import uuid
import logging
from dotenv import load_dotenv
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Email configuration with validation
def get_email_config():
    """Get and validate email configuration"""
    email_host = os.getenv("EMAIL_HOST")
    email_port_str = os.getenv("EMAIL_PORT")
    email_user = os.getenv("EMAIL_HOST_USER")
    email_pass = os.getenv("EMAIL_HOST_PASSWORD")
    
    # Validate all required environment variables
    if not all([email_host, email_port_str, email_user, email_pass]):
        missing = []
        if not email_host: missing.append("EMAIL_HOST")
        if not email_port_str: missing.append("EMAIL_PORT")
        if not email_user: missing.append("EMAIL_HOST_USER")
        if not email_pass: missing.append("EMAIL_HOST_PASSWORD")
        
        logger.error(f"Missing email configuration: {', '.join(missing)}")
        raise ValueError(f"Missing email configuration: {', '.join(missing)}")
    
    try:
        email_port = int(email_port_str)
    except ValueError:
        logger.error(f"Invalid EMAIL_PORT value: {email_port_str}")
        raise ValueError(f"EMAIL_PORT must be a valid integer, got: {email_port_str}")
    
    return email_host, email_port, email_user, email_pass

router = APIRouter(tags=["Authentication"])
db_dependency = Annotated[Session, Depends(get_db)]

# Ensure upload directory exists
UPLOAD_DIR = "uploads/profile_pics"
STATIC_DIR = "static/profile_pics"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

def send_email_verification(user_email: str, user_first_name: str, verification_code: str):
    """Send email verification code with proper error handling"""
    try:
        # Get email configuration
        email_host, email_port, email_user, email_pass = get_email_config()
        
        logger.info(f"Attempting to send verification email to {user_email}")
        logger.info(f"Using SMTP server: {email_host}:{email_port}")
        
        # Create email message
        msg = EmailMessage()
        msg["Subject"] = "DreamBox Email Verification Code"
        msg["From"] = email_user
        msg["To"] = user_email
        
        # Email content
        email_body = f"""Hello {user_first_name},

Your verification code is: {verification_code}

This code expires in 10 minutes.

If you didn't request this code, please ignore this email.

Thanks,
DreamBox Team"""
        
        msg.set_content(email_body)
        
        # Send email with detailed error handling
        try:
            with smtplib.SMTP(email_host, email_port) as smtp:
                smtp.set_debuglevel(1)  # Enable debug mode (prints SMTP logs)

                # Only start TLS if using STARTTLS port (587)
                if email_port == 587:
                    logger.info("Starting TLS encryption...")
                    smtp.starttls()

                logger.info("Logging in to SMTP server...")
                smtp.login(email_user, email_pass)

                logger.info("Sending verification email...")
                smtp.send_message(msg)

                logger.info(f"Email sent successfully to {user_email}")
                return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Email service authentication failed. Please contact support."
            )
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipients refused: {e}")
            raise HTTPException(
                status_code=400, 
                detail="Invalid email address. Please check your email and try again."
            )
        except smtplib.SMTPServerDisconnected as e:
            logger.error(f"SMTP server disconnected: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Email service temporarily unavailable. Please try again in a few minutes."
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Email service error: {str(e)}"
            )
        except ConnectionRefusedError as e:
            logger.error(f"Connection refused to email server: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Cannot connect to email service. Please contact support."
            )
        except Exception as e:
            logger.error(f"Unexpected error sending email: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to send email: {str(e)}"
            )
            
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Email service configuration error. Please contact support."
        )
    except Exception as e:
        logger.error(f"Unexpected error in email sending: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Email service is temporarily unavailable. Please try again later."
        )

@router.post("/register")
def register(user_data: UserCreate, db: db_dependency):
    logger.info(f"Registration attempt for email: {user_data.email}")
    
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
    
    logger.info(f"User registered successfully: {new_user.id}")

    # Create a proper JWT token
    token = create_access_token({"user_id": str(new_user.id)})

    return {
        "message": "User registered successfully. Proceed to email verification.",
        "access_token": token,
        "user_id": str(new_user.id),
        "first_name": new_user.first_name,
    }


@router.post("/send-verification-code")
def send_verification_code(data: dict, db: db_dependency):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    logger.info(f"Sending verification code to: {email}")
        
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User already verified")

    # Generate verification code
    code = ''.join(str(random.randint(0, 9)) for _ in range(6))
    expiry = datetime.now() + timedelta(minutes=10)

    # Save to database
    user.email_verification_code = code
    user.email_code_expiry = expiry
    db.commit()
    
    logger.info(f"Generated verification code for user {user.id}: {code}")

    # Send email
    send_email_verification(user.email, user.first_name, code)

    return {"message": "Verification code sent successfully"}


@router.post("/verify-email")
def verify_email(data: EmailVerificationInput, db: db_dependency):
    logger.info(f"Email verification attempt for: {data.email}")
    
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
        logger.warning(f"Invalid verification code attempt for user {user.id}")
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Verify user
    user.is_verified = True
    user.email_verification_code = None
    user.email_code_expiry = None
    db.commit()
    
    logger.info(f"Email verified successfully for user {user.id}")

    return {"message": "Email verified successfully ✅."}


@router.post("/resend-code")
def resend_verification_code(data: ResendCodeInput, db: db_dependency):
    logger.info(f"Resend code request for: {data.email}")
    
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="User is already verified")

    # Generate new verification code
    code = ''.join(str(random.randint(0, 9)) for _ in range(6))
    expiry = datetime.now() + timedelta(minutes=10)

    # Save to database
    user.email_verification_code = code
    user.email_code_expiry = expiry
    db.commit()
    
    logger.info(f"Generated new verification code for user {user.id}: {code}")

    # Send email
    send_email_verification(user.email, user.first_name, code)

    return {"message": "Verification code resent successfully ✅"}

@router.post("/login")
def login(user_data: LoginRequest, db: db_dependency):
    logger.info(f"Login attempt for email: {user_data.email}")
    
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        logger.warning(f"Invalid login attempt for email: {user_data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": str(user.id)})
    
    logger.info(f"Successful login for user {user.id}")

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
def verify_user_pin(data: SetPinInput, current_user: User = Depends(get_current_user)):
    if not current_user.pin:
        raise HTTPException(status_code=400, detail="No PIN set.")
    if not verify_pin(data.pin, current_user.pin):
        raise HTTPException(status_code=401, detail="Incorrect PIN")
    return {"message": "PIN verified successfully."}

@router.post("/upload-profile-picture")
def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only JPEG, PNG, and GIF files are allowed."
        )
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=400, 
            detail="File too large. Maximum size is 5MB."
        )

    try:
        # Create directories if they don't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(STATIC_DIR, exist_ok=True)

        # Generate unique filename
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in ["jpg", "jpeg", "png", "gif"]:
            file_extension = "jpg"
            
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Save to both upload and static directories
        upload_path = os.path.join(UPLOAD_DIR, unique_filename)
        static_path = os.path.join(STATIC_DIR, unique_filename)

        # Save the file
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Copy to static directory for serving
        shutil.copy2(upload_path, static_path)

        # Remove old profile picture if exists
        if current_user.profile_picture_url:
            try:
                # Extract filename from old URL
                old_filename = current_user.profile_picture_url.split("/")[-1]
                old_upload_path = os.path.join(UPLOAD_DIR, old_filename)
                old_static_path = os.path.join(STATIC_DIR, old_filename)
                
                # Remove old files
                if os.path.exists(old_upload_path):
                    os.remove(old_upload_path)
                if os.path.exists(old_static_path):
                    os.remove(old_static_path)
            except Exception as e:
                logger.warning(f"Could not remove old profile picture: {e}")

        # Update user profile with the static URL path
        profile_picture_url = f"/static/profile_pics/{unique_filename}"
        current_user.profile_picture_url = profile_picture_url
        
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

        return {
            "message": "Profile picture uploaded successfully",
            "url": profile_picture_url
        }

    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to upload profile picture: {str(e)}"
        )

@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    return JSONResponse(
        content={"message": "Logged out successfully."},
        status_code=status.HTTP_200_OK
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "date_of_birth": current_user.date_of_birth,
        "profile_picture_url": current_user.profile_picture_url,
    }