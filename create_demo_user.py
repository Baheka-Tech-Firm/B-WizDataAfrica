"""
Script to create a demo user for testing the African Market Data Platform.
"""
import os
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

# Create a minimal Flask app for creating the user
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy with the Base class
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Define minimal User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

def create_demo_user():
    """Create a demo user for testing."""
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