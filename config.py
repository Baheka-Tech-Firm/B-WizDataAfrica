import os

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Database 
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost/african_market_data")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Scraping settings
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    REQUEST_TIMEOUT = 30  # seconds
    
    # API settings
    API_TOKEN_EXPIRATION = 7 * 24 * 3600  # 7 days in seconds
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/african_market_data_test'
    
class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
# Default config
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Data sources configuration
STOCK_EXCHANGES = {
    'JSE': {
        'name': 'Johannesburg Stock Exchange',
        'country': 'South Africa',
        'currency': 'ZAR',
        'url': 'https://www.jse.co.za',
        'timezone': 'Africa/Johannesburg'
    },
    'NGX': {
        'name': 'Nigerian Exchange Group',
        'country': 'Nigeria',
        'currency': 'NGN',
        'url': 'https://ngxgroup.com',
        'timezone': 'Africa/Lagos'
    },
    'BRVM': {
        'name': 'Bourse Régionale des Valeurs Mobilières',
        'country': 'West Africa',
        'currency': 'XOF',
        'url': 'https://www.brvm.org',
        'timezone': 'Africa/Abidjan'
    }
}

# Central banks configuration
CENTRAL_BANKS = {
    'SARB': {
        'name': 'South African Reserve Bank',
        'country': 'South Africa',
        'url': 'https://www.resbank.co.za',
        'indicators': ['interest_rate', 'inflation', 'exchange_rate']
    },
    'CBN': {
        'name': 'Central Bank of Nigeria',
        'country': 'Nigeria',
        'url': 'https://www.cbn.gov.ng',
        'indicators': ['interest_rate', 'inflation', 'exchange_rate']
    },
    'BCEAO': {
        'name': 'Central Bank of West African States',
        'country': 'West Africa',
        'url': 'https://www.bceao.int',
        'indicators': ['interest_rate', 'inflation', 'exchange_rate']
    }
}
