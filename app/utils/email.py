import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()  

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

def send_email_verification_code(email: str, code: str):
    msg = EmailMessage()
    msg["Subject"] = "Your DreamBox Verification Code"
    msg["From"] = EMAIL_HOST_USER
    msg["To"] = email
    msg.set_content(f"Hello,\n\nYour verification code is: {code}\n\nThank you for using DreamBox.")

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as smtp:
            smtp.starttls() 
            smtp.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            smtp.send_message(msg)
            print(f"Email sent to {email} ✅")
    except Exception as e:
        print("Failed to send email ❌:", str(e))
