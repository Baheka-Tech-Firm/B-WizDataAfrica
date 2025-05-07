import logging
from app import app
from api.routes import register_api_routes
from tasks.scheduler import start_scheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Register API routes
register_api_routes(app)

# Start the scheduler for data collection tasks
start_scheduler()

if __name__ == "__main__":
    logger.info("Starting African Market Data Platform")
    app.run(host="0.0.0.0", port=5000, debug=True)
