from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from app.routes import auth, goals, payments, transactions, account_statement, wallets, auto_save, paystack_webhooks
# Create FastAPI app
app = FastAPI(title="DreamBox API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directories if they don't exist
os.makedirs("static/profile_pics", exist_ok=True)

# Mount static files - This is crucial for serving profile pictures
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include your routers

app.include_router(auth.router)
app.include_router(goals.router)
app.include_router(payments.router) 
app.include_router(transactions.router)
app.include_router(account_statement.router)
app.include_router(wallets.router)
app.include_router(auto_save.router)
app.include_router(paystack_webhooks.router) 

@app.get("/")
def read_root():
    return {"message": "DreamBox API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}