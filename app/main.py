from fastapi import FastAPI
from app.routes import auth, goals  
from app.core.database import engine, Base 

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(goals.router)