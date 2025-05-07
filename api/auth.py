import logging
import secrets
from datetime import datetime, timedelta
from models import User

logger = logging.getLogger(__name__)

class TokenAuth:
    """Token-based authentication for the API."""
    
    def __init__(self, db_session=None):
        """
        Initialize the token auth service.
        
        Args:
            db_session: Optional SQLAlchemy database session, used for testing
        """
        self.db_session = db_session
        # In-memory token store: {token: {'user_id': id, 'expires': datetime}}
        self.tokens = {}
    
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
        token = secrets.token_urlsafe(32)
        
        # Store token info
        expires = datetime.now() + timedelta(seconds=expiration)
        self.tokens[token] = {
            'user_id': user.id,
            'expires': expires
        }
        
        logger.debug(f"Generated token for user {user.id}, expires {expires}")
        return token
    
    def validate_token(self, token):
        """
        Validate a token and return the associated user.
        
        Args:
            token: Token string to validate
            
        Returns:
            User: User instance if token is valid, None otherwise
        """
        if token not in self.tokens:
            logger.debug(f"Token not found: {token[:10]}...")
            return None
        
        token_info = self.tokens[token]
        
        # Check expiration
        if token_info['expires'] < datetime.now():
            logger.debug(f"Token expired: {token[:10]}...")
            # Clean up expired token
            del self.tokens[token]
            return None
        
        # Get user
        from app import db
        user = db.session.query(User).get(token_info['user_id'])
        if not user:
            logger.warning(f"Token refers to non-existent user: {token_info['user_id']}")
            # Clean up invalid token
            del self.tokens[token]
            return None
        
        return user
    
    def revoke_token(self, token):
        """
        Revoke a token.
        
        Args:
            token: Token string to revoke
            
        Returns:
            bool: True if token was revoked, False if token wasn't found
        """
        if token in self.tokens:
            del self.tokens[token]
            logger.debug(f"Revoked token: {token[:10]}...")
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
        count = 0
        tokens_to_remove = []
        
        for token, info in self.tokens.items():
            if info['user_id'] == user_id:
                tokens_to_remove.append(token)
                count += 1
        
        for token in tokens_to_remove:
            del self.tokens[token]
        
        logger.debug(f"Revoked {count} tokens for user {user_id}")
        return count
