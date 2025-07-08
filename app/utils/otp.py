import random
from datetime import datetime, timedelta

def generate_otp(length: int = 6) -> str:
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def otp_expiry(minutes=5):
    return datetime.now() + timedelta(minutes=minutes)
