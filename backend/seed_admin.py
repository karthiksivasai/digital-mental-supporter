"""Seed script to create admin user"""
import sys
from app.database import SessionLocal, engine, Base
from app.models import User
from app.auth import get_password_hash
from app.config import settings

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Check if admin exists
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    
    if admin:
        print(f"Admin user {settings.ADMIN_EMAIL} already exists")
    else:
        # Ensure password is not too long for bcrypt
        password = settings.ADMIN_PASSWORD[:72] if len(settings.ADMIN_PASSWORD) > 72 else settings.ADMIN_PASSWORD
        admin = User(
            email=settings.ADMIN_EMAIL,
            hashed_password=get_password_hash(password),
            is_admin=True,
            is_active=True,
            consent_given=True
        )
        db.add(admin)
        db.commit()
        print(f"Admin user created: {settings.ADMIN_EMAIL}")
        print(f"Password: {settings.ADMIN_PASSWORD}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

