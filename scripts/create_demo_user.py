"""
Script to create a demo user for testing the African Market Data Platform.
"""
import sys
import os
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from werkzeug.security import generate_password_hash
from models import User, APIToken
from app import db

def create_demo_user():
    """Create a demo user for testing."""
    # Create Flask app context
    from app import app
    with app.app_context():
        # Check if demo user already exists
        demo_user = User.query.filter_by(email='demo@example.com').first()
        
        if demo_user:
            print("Demo user already exists.")
            return demo_user
        
        # Create new demo user
        demo_user = User(
            username='demo_user',
            email='demo@example.com',
            password_hash=generate_password_hash('password123'),
            is_admin=False,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        
        try:
            db.session.add(demo_user)
            db.session.commit()
            print(f"Demo user created successfully: username=demo_user, email=demo@example.com, password=password123")
            return demo_user
        except Exception as e:
            db.session.rollback()
            print(f"Error creating demo user: {str(e)}")
            return None

if __name__ == "__main__":
    create_demo_user()