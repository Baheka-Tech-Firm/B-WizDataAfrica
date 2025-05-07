import logging
import atexit
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import current_app

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()

def setup_data_collection_tasks():
    """Setup scheduled tasks for data collection."""
    from app import app, db
    from etl.processor import ETLProcessor
    from tasks.market_summary import generate_market_summary
    
    with app.app_context():
        # Setup ETL processor task for each exchange
        def collect_jse_data():
            """Task to collect JSE data."""
            try:
                logger.info("Starting JSE data collection task")
                processor = ETLProcessor(db.session)
                results = processor.process_exchange_data('JSE')
                logger.info(f"JSE data collection completed: {results['stocks_processed']} stocks, {results['prices_processed']} prices")
            except Exception as e:
                logger.error(f"Error in JSE data collection task: {str(e)}")
        
        def collect_ngx_data():
            """Task to collect NGX data."""
            try:
                logger.info("Starting NGX data collection task")
                processor = ETLProcessor(db.session)
                results = processor.process_exchange_data('NGX')
                logger.info(f"NGX data collection completed: {results['stocks_processed']} stocks, {results['prices_processed']} prices")
            except Exception as e:
                logger.error(f"Error in NGX data collection task: {str(e)}")
        
        def collect_brvm_data():
            """Task to collect BRVM data."""
            try:
                logger.info("Starting BRVM data collection task")
                processor = ETLProcessor(db.session)
                results = processor.process_exchange_data('BRVM')
                logger.info(f"BRVM data collection completed: {results['stocks_processed']} stocks, {results['prices_processed']} prices")
            except Exception as e:
                logger.error(f"Error in BRVM data collection task: {str(e)}")
        
        def generate_daily_market_summary():
            """Task to generate daily market summary."""
            try:
                logger.info("Starting daily market summary generation")
                generate_market_summary(db.session)
                logger.info("Daily market summary generation completed")
            except Exception as e:
                logger.error(f"Error in daily market summary generation: {str(e)}")
        
        # Schedule tasks - run at different times to avoid overloading resources
        # JSE data - Run every weekday at 16:30 (after close)
        scheduler.add_job(
            collect_jse_data,
            CronTrigger(day_of_week='mon-fri', hour=16, minute=30),
            id='collect_jse_data',
            replace_existing=True
        )
        
        # NGX data - Run every weekday at 17:00 (after close)
        scheduler.add_job(
            collect_ngx_data,
            CronTrigger(day_of_week='mon-fri', hour=17, minute=0),
            id='collect_ngx_data',
            replace_existing=True
        )
        
        # BRVM data - Run every weekday at 17:30 (after close)
        scheduler.add_job(
            collect_brvm_data,
            CronTrigger(day_of_week='mon-fri', hour=17, minute=30),
            id='collect_brvm_data',
            replace_existing=True
        )
        
        # Market summary - Run every weekday at 18:00 (after all data collection)
        scheduler.add_job(
            generate_daily_market_summary,
            CronTrigger(day_of_week='mon-fri', hour=18, minute=0),
            id='generate_market_summary',
            replace_existing=True
        )
        
        logger.info("Scheduled data collection tasks")

def start_scheduler():
    """Start the background scheduler for periodic tasks."""
    if scheduler.running:
        logger.warning("Scheduler already running")
        return
    
    # Setup tasks
    setup_data_collection_tasks()
    
    # Add testing job to run right away for development
    def test_job():
        logger.info("Test scheduler job running at " + str(datetime.now()))
    
    scheduler.add_job(
        test_job,
        'interval',
        minutes=5,
        id='test_job',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started")
    
    # Register shutdown handler
    atexit.register(lambda: scheduler.shutdown())
