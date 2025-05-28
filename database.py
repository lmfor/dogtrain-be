from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")   

# Create a new SQLAlchemy engine instance
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
    )

Base = declarative_base()