import logging
import secrets
from datetime import datetime, timedelta
from models import User, APIToken
from app import db

logger = logging.getLogger(__name__)

class TokenAuth:
    """Token-based authentication for the API."""
    
    def __init__(self, db_session=None):
        """
        Initialize the token auth service.
        
        Args:
            db_session: Optional SQLAlchemy database session, used for testing
        """
        self.db_session = db_session or db.session
    
    def generate_token(self, user, expiration=None):
        """
        Generate a token for a user.
        
        Args:
            user: User model instance
            expiration: Optional expiration time in seconds
            
        Returns:
            str: Generated token
        """
        if not expiration:
            from flask import current_app
            expiration = current_app.config.get('API_TOKEN_EXPIRATION', 604800)  # Default 7 days
        
        # Generate a random token
        token_str = secrets.token_urlsafe(32)
        
        # Calculate expiration date
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        
        # Create a database token
        token = APIToken(token=token_str, user_id=user.id, expires_at=expires_at)
        self.db_session.add(token)
        self.db_session.commit()
        
        logger.debug(f"Generated token for user {user.id}, expires {expires_at}")
        return token_str
    
    def validate_token(self, token_str):
        """
        Validate a token and return the associated user.
        
        Args:
            token_str: Token string to validate
            
        Returns:
            User: User instance if token is valid, None otherwise
        """
        # Find token in database
        token = self.db_session.query(APIToken).filter_by(token=token_str).first()
        
        if not token:
            logger.debug(f"Token not found: {token_str[:10]}...")
            return None
        
        # Check expiration
        if token.is_expired():
            logger.debug(f"Token expired: {token_str[:10]}...")
            # Clean up expired token
            self.db_session.delete(token)
            self.db_session.commit()
            return None
        
        # Return the associated user
        user = token.user
        if not user:
            logger.warning(f"Token refers to non-existent user: {token.user_id}")
            # Clean up invalid token
            self.db_session.delete(token)
            self.db_session.commit()
            return None
        
        return user
    
    def revoke_token(self, token_str):
        """
        Revoke a token.
        
        Args:
            token_str: Token string to revoke
            
        Returns:
            bool: True if token was revoked, False if token wasn't found
        """
        token = self.db_session.query(APIToken).filter_by(token=token_str).first()
        
        if token:
            self.db_session.delete(token)
            self.db_session.commit()
            logger.debug(f"Revoked token: {token_str[:10]}...")
            return True
        return False
    
    def revoke_user_tokens(self, user_id):
        """
        Revoke all tokens for a user.
        
        Args:
            user_id: User ID to revoke tokens for
            
        Returns:
            int: Number of tokens revoked
        """
        tokens = self.db_session.query(APIToken).filter_by(user_id=user_id).all()
        count = len(tokens)
        
        for token in tokens:
            self.db_session.delete(token)
        
        self.db_session.commit()
        logger.debug(f"Revoked {count} tokens for user {user_id}")
        return count
