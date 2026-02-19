# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv


load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ CRITICAL ERROR: 'DATABASE_URL' not found. Please create a .env file with your Neon connection string.")


if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


DATABASE_URL = DATABASE_URL.strip().strip('"').strip("'")


try:
    engine = create_engine(
        DATABASE_URL,
        
        pool_pre_ping=True, 
        
        
        pool_recycle=1200,
        
        
        pool_size=10,
        max_overflow=20,
        
        
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )
    
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Database Engine Initialized Successfully")

except Exception as e:
    print(f"❌ Failed to connect to database: {e}")
    raise e

def init_db():
    """Initializes the database tables (Run this once on startup)."""
    try:
        
        from models import Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database Tables Verified/Created.")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")