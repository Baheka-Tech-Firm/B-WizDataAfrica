import requests
import logging
from abc import ABC, abstractmethod
from datetime import datetime
import trafilatura
from config import Config

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all data scrapers."""
    
    def __init__(self, source_url, exchange_code=None):
        """
        Initialize the scraper with source URL and exchange code.
        
        Args:
            source_url (str): URL to scrape data from
            exchange_code (str, optional): Exchange code (JSE, NGX, BRVM)
        """
        self.source_url = source_url
        self.exchange_code = exchange_code
        self.headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    def fetch_html(self, url=None):
        """
        Fetch HTML content from the specified URL.
        
        Args:
            url (str, optional): URL to fetch. If None, use self.source_url
            
        Returns:
            str: HTML content or None if failed
        """
        target_url = url or self.source_url
        try:
            logger.info(f"Fetching HTML from {target_url}")
            response = requests.get(
                target_url, 
                headers=self.headers, 
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {target_url}: {e}")
            return None
    
    def extract_text_content(self, html):
        """
        Extract the main text content from HTML using trafilatura.
        
        Args:
            html (str): HTML content to extract from
            
        Returns:
            str: Extracted text content
        """
        try:
            return trafilatura.extract(html)
        except Exception as e:
            logger.error(f"Error extracting text content: {e}")
            return None
    
    @abstractmethod
    def scrape_stocks(self):
        """
        Scrape stock data from the source.
        
        Returns:
            list: List of stock dictionaries
        """
        pass
    
    @abstractmethod
    def scrape_stock_prices(self, ticker=None):
        """
        Scrape stock price data from the source.
        
        Args:
            ticker (str, optional): Specific ticker to scrape prices for
            
        Returns:
            dict: Dictionary of stock prices by ticker
        """
        pass
    
    @abstractmethod
    def scrape_indices(self):
        """
        Scrape index data from the source.
        
        Returns:
            list: List of index dictionaries
        """
        pass
    
    def log_scrape_start(self):
        """Log the start of a scraping operation."""
        logger.info(f"Starting scrape for {self.exchange_code or 'unknown'} at {datetime.now()}")
    
    def log_scrape_complete(self, data_type, count):
        """Log the completion of a scraping operation."""
        logger.info(f"Completed scraping {count} {data_type} from {self.exchange_code or 'unknown'}")
