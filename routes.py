from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Stock, StockPrice, Exchange, MarketSummary
from app import db
import logging

logger = logging.getLogger(__name__)

def configure_routes(app):
    @app.route('/')
    def index():
        latest_summaries = MarketSummary.query.order_by(MarketSummary.date.desc()).limit(5).all()
        return render_template('index.html', summaries=latest_summaries)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get exchanges for the dashboard
        exchanges = Exchange.query.all()
        return render_template('dashboard.html', exchanges=exchanges)

    @app.route('/stocks')
    @login_required
    def stocks():
        exchange_id = request.args.get('exchange_id')
        if exchange_id:
            stocks = Stock.query.filter_by(exchange_id=exchange_id).all()
            exchange = Exchange.query.get(exchange_id)
        else:
            stocks = Stock.query.all()
            exchange = None
        
        exchanges = Exchange.query.all()
        return render_template('stocks.html', stocks=stocks, exchanges=exchanges, current_exchange=exchange)

    @app.route('/stock/<string:ticker>')
    @login_required
    def stock_detail(ticker):
        stock = Stock.query.filter_by(ticker=ticker).first_or_404()
        prices = StockPrice.query.filter_by(stock_id=stock.id).order_by(StockPrice.date.desc()).limit(30).all()
        # Reverse to get chronological order for charts
        prices = prices[::-1]
        return render_template('stock_detail.html', stock=stock, prices=prices)

    @app.route('/market-summary')
    @login_required
    def market_summary():
        summaries = MarketSummary.query.order_by(MarketSummary.date.desc()).limit(10).all()
        return render_template('market_summary.html', summaries=summaries)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            user = User.query.filter_by(email=email).first()
            
            # Check if user exists and password is correct
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid email or password', 'danger')
                
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Check if user already exists
            user_exists = User.query.filter_by(email=email).first()
            username_exists = User.query.filter_by(username=username).first()
            
            if user_exists:
                flash('Email already registered', 'danger')
            elif username_exists:
                flash('Username already taken', 'danger')
            else:
                # Create new user
                new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
                db.session.add(new_user)
                db.session.commit()
                
                flash('Registration successful! You can now log in.', 'success')
                return redirect(url_for('login'))
                
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return render_template('500.html'), 500
