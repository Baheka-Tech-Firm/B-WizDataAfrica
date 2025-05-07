import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataTransformer:
    """Transforms raw scraped data into a format ready for database loading."""
    
    def transform_stocks(self, raw_stocks, exchange_code):
        """
        Transform raw stock data.
        
        Args:
            raw_stocks (list): List of raw stock dictionaries
            exchange_code (str): Exchange code
            
        Returns:
            list: List of transformed stock dictionaries
        """
        transformed = []
        
        for stock in raw_stocks:
            try:
                # Create a standardized stock dictionary
                transformed_stock = {
                    'ticker': stock.get('ticker', '').strip().upper(),
                    'name': stock.get('name', '').strip(),
                    'exchange_code': exchange_code,
                    'sector': stock.get('sector', '').strip() if stock.get('sector') else None,
                    'currency': stock.get('currency'),
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                
                # Validate required fields
                if not transformed_stock['ticker'] or not transformed_stock['name']:
                    logger.warning(f"Skipping stock with missing required fields: {stock}")
                    continue
                
                transformed.append(transformed_stock)
            except Exception as e:
                logger.error(f"Error transforming stock {stock.get('ticker', 'unknown')}: {str(e)}")
        
        logger.info(f"Transformed {len(transformed)} stocks for {exchange_code}")
        return transformed
    
    def transform_stock_prices(self, raw_prices, exchange_code):
        """
        Transform raw stock price data.
        
        Args:
            raw_prices (dict): Dictionary of raw price lists by ticker
            exchange_code (str): Exchange code
            
        Returns:
            list: List of transformed price dictionaries
        """
        transformed = []
        
        for ticker, prices in raw_prices.items():
            for price in prices:
                try:
                    # Create a standardized price dictionary
                    transformed_price = {
                        'ticker': ticker.strip().upper(),
                        'exchange_code': exchange_code,
                        'date': price.get('date', datetime.now().strftime('%Y-%m-%d')),
                        'close_price': price.get('close_price'),
                        'open_price': price.get('open_price'),
                        'high_price': price.get('high_price'),
                        'low_price': price.get('low_price'),
                        'volume': price.get('volume'),
                        'change_percent': price.get('change_percent')
                    }
                    
                    # Validate required fields
                    if not transformed_price['ticker'] or transformed_price['close_price'] is None:
                        logger.warning(f"Skipping price with missing required fields: {price}")
                        continue
                    
                    # Ensure date is in proper format
                    if isinstance(transformed_price['date'], str):
                        try:
                            # Parse and reformat to ensure consistency
                            date_obj = datetime.strptime(transformed_price['date'], '%Y-%m-%d')
                            transformed_price['date'] = date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            # If date format is wrong, use today's date
                            transformed_price['date'] = datetime.now().strftime('%Y-%m-%d')
                            logger.warning(f"Invalid date format for {ticker}, using today's date")
                    
                    transformed.append(transformed_price)
                except Exception as e:
                    logger.error(f"Error transforming price for {ticker}: {str(e)}")
        
        logger.info(f"Transformed {len(transformed)} price points for {exchange_code}")
        return transformed
    
    def transform_indices(self, raw_indices, exchange_code):
        """
        Transform raw index data.
        
        Args:
            raw_indices (list): List of raw index dictionaries
            exchange_code (str): Exchange code
            
        Returns:
            tuple: (transformed_indices, transformed_values)
        """
        transformed_indices = []
        transformed_values = []
        today = datetime.now().strftime('%Y-%m-%d')
        
        for index in raw_indices:
            try:
                # Create a standardized index dictionary
                transformed_index = {
                    'code': index.get('code', '').strip().upper(),
                    'name': index.get('name', '').strip(),
                    'exchange_code': exchange_code,
                    'last_updated': today
                }
                
                # Validate required fields
                if not transformed_index['code'] or not transformed_index['name']:
                    logger.warning(f"Skipping index with missing required fields: {index}")
                    continue
                
                transformed_indices.append(transformed_index)
                
                # Create corresponding index value
                if index.get('value') is not None:
                    transformed_value = {
                        'index_code': transformed_index['code'],
                        'exchange_code': exchange_code,
                        'date': today,
                        'value': index.get('value'),
                        'change_percent': index.get('change_percent')
                    }
                    transformed_values.append(transformed_value)
            except Exception as e:
                logger.error(f"Error transforming index {index.get('code', 'unknown')}: {str(e)}")
        
        logger.info(f"Transformed {len(transformed_indices)} indices and {len(transformed_values)} values for {exchange_code}")
        return transformed_indices, transformed_values
