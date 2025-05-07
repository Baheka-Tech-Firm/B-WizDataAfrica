from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import UniqueConstraint

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationship with API tokens
    tokens = db.relationship('APIToken', backref='user', lazy=True, cascade='all, delete-orphan')
    
class APIToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        """Check if the token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<APIToken {self.token[:8]}... expires: {self.expires_at}>'

class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    country = db.Column(db.String(100), nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    website = db.Column(db.String(200))
    timezone = db.Column(db.String(50))
    description = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    stocks = db.relationship('Stock', backref='exchange', lazy=True)
    
    def __repr__(self):
        return f'<Exchange {self.code}>'
    
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    sector = db.Column(db.String(100))
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    currency = db.Column(db.String(10))
    description = db.Column(db.Text)
    website = db.Column(db.String(200))
    market_cap = db.Column(db.Float)
    outstanding_shares = db.Column(db.BigInteger)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    prices = db.relationship('StockPrice', backref='stock', lazy=True)
    
    # Unique constraint for ticker and exchange
    __table_args__ = (UniqueConstraint('ticker', 'exchange_id', name='_ticker_exchange_uc'),)
    
    def __repr__(self):
        return f'<Stock {self.ticker}>'

class StockPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    open_price = db.Column(db.Float)
    close_price = db.Column(db.Float, nullable=False)
    high_price = db.Column(db.Float)
    low_price = db.Column(db.Float)
    volume = db.Column(db.BigInteger)
    change_percent = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint for stock and date
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='_stock_date_uc'),)
    
    def __repr__(self):
        return f'<StockPrice {self.stock.ticker} {self.date}>'

class Index(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    values = db.relationship('IndexValue', backref='index', lazy=True)
    
    def __repr__(self):
        return f'<Index {self.code}>'

class IndexValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    index_id = db.Column(db.Integer, db.ForeignKey('index.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    change_percent = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint for index and date
    __table_args__ = (UniqueConstraint('index_id', 'date', name='_index_date_uc'),)
    
    def __repr__(self):
        return f'<IndexValue {self.index.code} {self.date}>'

class MacroIndicator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'GDP', 'Inflation', 'FX'
    unit = db.Column(db.String(50))
    description = db.Column(db.Text)
    source = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    values = db.relationship('MacroIndicatorValue', backref='indicator', lazy=True)
    
    # Unique constraint for code and country
    __table_args__ = (UniqueConstraint('code', 'country', name='_code_country_uc'),)
    
    def __repr__(self):
        return f'<MacroIndicator {self.country} {self.code}>'

class MacroIndicatorValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    indicator_id = db.Column(db.Integer, db.ForeignKey('macro_indicator.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint for indicator and date
    __table_args__ = (UniqueConstraint('indicator_id', 'date', name='_indicator_date_uc'),)
    
    def __repr__(self):
        return f'<MacroIndicatorValue {self.indicator.code} {self.date}>'

class MarketSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False, unique=True)
    content = db.Column(db.Text, nullable=False)
    highlights = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MarketSummary {self.date}>'

class DataSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'stock', 'macro', 'news'
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'))
    country = db.Column(db.String(100))
    scraper_class = db.Column(db.String(100))
    enabled = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    schedule_interval = db.Column(db.String(100), default='daily')  # 'daily', 'weekly', 'hourly'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DataSource {self.name}>'
