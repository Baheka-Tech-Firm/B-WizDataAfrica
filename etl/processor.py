import logging
from datetime import datetime
from etl.transformer import DataTransformer
from etl.loader import DataLoader
from scrapers.jse_scraper import JSEScraper
from scrapers.ngx_scraper import NGXScraper
from scrapers.brvm_scraper import BRVMScraper
from models import Exchange, Stock, StockPrice, Index, IndexValue, DataSource

logger = logging.getLogger(__name__)

class ETLProcessor:
    """Main ETL processor that orchestrates the data pipeline."""
    
    def __init__(self, db_session):
        """
        Initialize the ETL processor.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.transformer = DataTransformer()
        self.loader = DataLoader(db_session)
        
        # Initialize scrapers
        self.scrapers = {
            'JSE': JSEScraper(),
            'NGX': NGXScraper(),
            'BRVM': BRVMScraper()
        }
    
    def process_exchange_data(self, exchange_code):
        """
        Process all data for a specific exchange.
        
        Args:
            exchange_code (str): Exchange code (JSE, NGX, BRVM)
            
        Returns:
            dict: Summary of processed data
        """
        logger.info(f"Processing data for exchange: {exchange_code}")
        summary = {
            'exchange': exchange_code,
            'start_time': datetime.now(),
            'stocks_processed': 0,
            'prices_processed': 0,
            'indices_processed': 0,
            'errors': []
        }
        
        try:
            # Get the scraper for this exchange
            scraper = self.scrapers.get(exchange_code)
            if not scraper:
                error_msg = f"No scraper configured for exchange {exchange_code}"
                logger.error(error_msg)
                summary['errors'].append(error_msg)
                return summary
            
            # Process stocks data
            self._process_stocks(scraper, exchange_code, summary)
            
            # Process stock prices
            self._process_stock_prices(scraper, exchange_code, summary)
            
            # Process indices
            self._process_indices(scraper, exchange_code, summary)
            
        except Exception as e:
            error_msg = f"Error processing {exchange_code}: {str(e)}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
        
        summary['end_time'] = datetime.now()
        summary['duration'] = (summary['end_time'] - summary['start_time']).total_seconds()
        
        # Update the data source record
        self._update_data_source(exchange_code, summary)
        
        return summary
    
    def _process_stocks(self, scraper, exchange_code, summary):
        """Process stock listings for an exchange."""
        try:
            # Scrape stocks data
            raw_stocks = scraper.scrape_stocks()
            
            if not raw_stocks:
                logger.warning(f"No stocks data retrieved for {exchange_code}")
                return
            
            # Transform the data
            transformed_stocks = self.transformer.transform_stocks(raw_stocks, exchange_code)
            
            # Load the data
            stocks_processed = self.loader.load_stocks(transformed_stocks, exchange_code)
            
            summary['stocks_processed'] = stocks_processed
            logger.info(f"Processed {stocks_processed} stocks for {exchange_code}")
            
        except Exception as e:
            error_msg = f"Error processing stocks for {exchange_code}: {str(e)}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
    
    def _process_stock_prices(self, scraper, exchange_code, summary):
        """Process stock prices for an exchange."""
        try:
            # Scrape stock prices data
            raw_prices = scraper.scrape_stock_prices()
            
            if not raw_prices:
                logger.warning(f"No stock prices retrieved for {exchange_code}")
                return
            
            # Transform the data
            transformed_prices = self.transformer.transform_stock_prices(raw_prices, exchange_code)
            
            # Load the data
            prices_processed = self.loader.load_stock_prices(transformed_prices, exchange_code)
            
            summary['prices_processed'] = prices_processed
            logger.info(f"Processed {prices_processed} price points for {exchange_code}")
            
        except Exception as e:
            error_msg = f"Error processing stock prices for {exchange_code}: {str(e)}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
    
    def _process_indices(self, scraper, exchange_code, summary):
        """Process indices for an exchange."""
        try:
            # Scrape indices data
            raw_indices = scraper.scrape_indices()
            
            if not raw_indices:
                logger.warning(f"No indices retrieved for {exchange_code}")
                return
            
            # Transform the data
            transformed_indices, transformed_values = self.transformer.transform_indices(raw_indices, exchange_code)
            
            # Load the data
            indices_processed = self.loader.load_indices(transformed_indices, transformed_values, exchange_code)
            
            summary['indices_processed'] = indices_processed
            logger.info(f"Processed {indices_processed} indices for {exchange_code}")
            
        except Exception as e:
            error_msg = f"Error processing indices for {exchange_code}: {str(e)}"
            logger.error(error_msg)
            summary['errors'].append(error_msg)
    
    def _update_data_source(self, exchange_code, summary):
        """Update the data source record with the latest run information."""
        try:
            # Find or create the data source record
            data_source = self.db_session.query(DataSource).filter_by(
                exchange_id=self.db_session.query(Exchange.id).filter_by(code=exchange_code).scalar(),
                type='stock'
            ).first()
            
            if not data_source:
                # This shouldn't happen in normal operation, but handle it gracefully
                logger.warning(f"No data source record found for {exchange_code}")
                return
            
            # Update the record
            data_source.last_run = datetime.now()
            
            # If there were errors, add them to the record
            if summary.get('errors'):
                error_str = "; ".join(summary['errors'])
                logger.warning(f"ETL errors for {exchange_code}: {error_str}")
            
            self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Error updating data source record for {exchange_code}: {str(e)}")
            self.db_session.rollback()
    
    def process_all_exchanges(self):
        """
        Process data for all configured exchanges.
        
        Returns:
            dict: Summary of all processing results
        """
        logger.info("Processing data for all exchanges")
        results = {}
        
        for exchange_code in self.scrapers.keys():
            results[exchange_code] = self.process_exchange_data(exchange_code)
        
        return results
