from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker 


DATABASE_URL = "postgresql://postgres:Ug?10976491@localhost/DreamBox" 

engine = create_engine(DATABASE_URL)  

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # Helps in talking to the database

Base = declarative_base() # The base class for defining database models.  

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
