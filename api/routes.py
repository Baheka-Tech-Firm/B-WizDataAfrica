import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request, abort, current_app, g
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy import desc
from models import (User, Exchange, Stock, StockPrice, 
                   Index, IndexValue, MacroIndicator, 
                   MacroIndicatorValue, MarketSummary)
from api.serializers import (serialize_exchange, serialize_stock, 
                           serialize_stock_price, serialize_index, 
                           serialize_index_value, serialize_macro_indicator,
                           serialize_macro_value, serialize_market_summary)
from api.auth import TokenAuth

logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Authentication helper
token_auth = TokenAuth()

def token_required(f):
    """Decorator to require API token authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if the request has a token
        token = request.headers.get('X-API-Token')
        if not token:
            return jsonify({'error': 'API token is missing'}), 401
        
        # Validate the token
        user = token_auth.validate_token(token)
        if not user:
            return jsonify({'error': 'Invalid or expired API token'}), 401
        
        # Store the user in g for access in the view
        g.user = user
        return f(*args, **kwargs)
    return decorated

def register_api_routes(app):
    """Register API routes with the Flask app."""
    app.register_blueprint(api_bp)
    logger.info("API routes registered")

# API endpoints
@api_bp.route('/exchanges', methods=['GET'])
@token_required
def get_exchanges():
    """Get all exchanges."""
    exchanges = Exchange.query.all()
    return jsonify([serialize_exchange(exchange) for exchange in exchanges])

@api_bp.route('/exchanges/<string:code>', methods=['GET'])
@token_required
def get_exchange(code):
    """Get a specific exchange by code."""
    exchange = Exchange.query.filter_by(code=code).first_or_404()
    return jsonify(serialize_exchange(exchange))

@api_bp.route('/exchanges/<string:code>/stocks', methods=['GET'])
@token_required
def get_exchange_stocks(code):
    """Get all stocks for a specific exchange."""
    exchange = Exchange.query.filter_by(code=code).first_or_404()
    stocks = Stock.query.filter_by(exchange_id=exchange.id).all()
    return jsonify([serialize_stock(stock) for stock in stocks])

@api_bp.route('/stocks', methods=['GET'])
@token_required
def get_stocks():
    """Get stocks with optional filtering."""
    # Get query parameters
    exchange_code = request.args.get('exchange')
    sector = request.args.get('sector')
    ticker_filter = request.args.get('ticker')
    limit = int(request.args.get('limit', 100))
    
    # Build query
    query = Stock.query
    
    # Apply filters
    if exchange_code:
        exchange = Exchange.query.filter_by(code=exchange_code).first()
        if exchange:
            query = query.filter_by(exchange_id=exchange.id)
    
    if sector:
        query = query.filter(Stock.sector.ilike(f'%{sector}%'))
    
    if ticker_filter:
        query = query.filter(Stock.ticker.ilike(f'%{ticker_filter}%'))
    
    # Get results
    stocks = query.limit(limit).all()
    return jsonify([serialize_stock(stock) for stock in stocks])

@api_bp.route('/stocks/<string:exchange_code>/<string:ticker>', methods=['GET'])
@token_required
def get_stock(exchange_code, ticker):
    """Get a specific stock by exchange code and ticker."""
    exchange = Exchange.query.filter_by(code=exchange_code).first_or_404()
    stock = Stock.query.filter_by(exchange_id=exchange.id, ticker=ticker).first_or_404()
    return jsonify(serialize_stock(stock))

@api_bp.route('/stocks/<string:exchange_code>/<string:ticker>/prices', methods=['GET'])
@token_required
def get_stock_prices(exchange_code, ticker):
    """Get price history for a specific stock."""
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 30))
    
    # Find the stock
    exchange = Exchange.query.filter_by(code=exchange_code).first_or_404()
    stock = Stock.query.filter_by(exchange_id=exchange.id, ticker=ticker).first_or_404()
    
    # Build query
    query = StockPrice.query.filter_by(stock_id=stock.id)
    
    # Apply date filters
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(StockPrice.date >= start)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(StockPrice.date <= end)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Get results ordered by date
    prices = query.order_by(StockPrice.date.desc()).limit(limit).all()
    
    # Return results with stock information
    return jsonify({
        'stock': serialize_stock(stock),
        'prices': [serialize_stock_price(price) for price in prices]
    })

@api_bp.route('/indices', methods=['GET'])
@token_required
def get_indices():
    """Get indices with optional filtering."""
    # Get query parameters
    exchange_code = request.args.get('exchange')
    limit = int(request.args.get('limit', 100))
    
    # Build query
    query = Index.query
    
    # Apply filters
    if exchange_code:
        exchange = Exchange.query.filter_by(code=exchange_code).first()
        if exchange:
            query = query.filter_by(exchange_id=exchange.id)
    
    # Get results
    indices = query.limit(limit).all()
    return jsonify([serialize_index(index) for index in indices])

@api_bp.route('/indices/<string:exchange_code>/<string:code>', methods=['GET'])
@token_required
def get_index(exchange_code, code):
    """Get a specific index by exchange code and index code."""
    exchange = Exchange.query.filter_by(code=exchange_code).first_or_404()
    index = Index.query.filter_by(exchange_id=exchange.id, code=code).first_or_404()
    return jsonify(serialize_index(index))

@api_bp.route('/indices/<string:exchange_code>/<string:code>/values', methods=['GET'])
@token_required
def get_index_values(exchange_code, code):
    """Get value history for a specific index."""
    # Get query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = int(request.args.get('limit', 30))
    
    # Find the index
    exchange = Exchange.query.filter_by(code=exchange_code).first_or_404()
    index = Index.query.filter_by(exchange_id=exchange.id, code=code).first_or_404()
    
    # Build query
    query = IndexValue.query.filter_by(index_id=index.id)
    
    # Apply date filters
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(IndexValue.date >= start)
        except ValueError:
            return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(IndexValue.date <= end)
        except ValueError:
            return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
    
    # Get results ordered by date
    values = query.order_by(IndexValue.date.desc()).limit(limit).all()
    
    # Return results with index information
    return jsonify({
        'index': serialize_index(index),
        'values': [serialize_index_value(value) for value in values]
    })

@api_bp.route('/macro-indicators', methods=['GET'])
@token_required
def get_macro_indicators():
    """Get macro indicators with optional filtering."""
    # Get query parameters
    country = request.args.get('country')
    category = request.args.get('category')
    limit = int(request.args.get('limit', 100))
    
    # Build query
    query = MacroIndicator.query
    
    # Apply filters
    if country:
        query = query.filter_by(country=country)
    
    if category:
        query = query.filter_by(category=category)
    
    # Get results
    indicators = query.limit(limit).all()
    return jsonify([serialize_macro_indicator(indicator) for indicator in indicators])

@api_bp.route('/market-summaries', methods=['GET'])
@token_required
def get_market_summaries():
    """Get recent market summaries."""
    # Get query parameters
    limit = int(request.args.get('limit', 10))
    
    # Get results
    summaries = MarketSummary.query.order_by(MarketSummary.date.desc()).limit(limit).all()
    return jsonify([serialize_market_summary(summary) for summary in summaries])

@api_bp.route('/market-summaries/<string:date>', methods=['GET'])
@token_required
def get_market_summary(date):
    """Get a specific market summary by date."""
    try:
        summary_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    summary = MarketSummary.query.filter_by(date=summary_date).first_or_404()
    return jsonify(serialize_market_summary(summary))

@api_bp.route('/token', methods=['POST'])
@login_required
def get_token():
    """Generate an API token for the authenticated user."""
    # This endpoint requires a logged-in user (via the web interface)
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Generate a token
    token = token_auth.generate_token(current_user)
    
    return jsonify({
        'token': token,
        'expires_at': (datetime.now() + timedelta(seconds=current_app.config.get('API_TOKEN_EXPIRATION', 604800))).isoformat(),
        'user_id': current_user.id
    })

@api_bp.route('/token/validate', methods=['GET'])
@token_required
def validate_token():
    """Validate the provided API token."""
    # If we got here, the token is valid (due to @token_required decorator)
    return jsonify({
        'valid': True,
        'user_id': g.user.id
    })

# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@api_bp.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
