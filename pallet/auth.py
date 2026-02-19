# auth.py
import bcrypt
from sqlalchemy.orm import Session
from models import User
from datetime import datetime

def hash_password(password: str):
    """Securely hashes a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password, hashed_password):
    """Checks a plain text password against the stored hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(db: Session, username, password):
    """Verifies credentials and updates last login time."""
    user = db.query(User).filter(User.username == username).first()
    if user and verify_password(password, user.password_hash):
        
        user.last_login = datetime.utcnow()
        db.commit()
        return user
    return None

def create_initial_admin(db: Session):
    """Creates a default admin user (admin/admin123) if the table is empty."""
    if not db.query(User).first():
        print("⚠️ No users found. Creating default 'admin' account.")
        admin = User(
            username="admin", 
            password_hash=hash_password("admin123"), 
            role="Commander"
        )
        db.add(admin)
        db.commit()
        print("✅ Default Admin Created: User='admin', Pass='admin123'")