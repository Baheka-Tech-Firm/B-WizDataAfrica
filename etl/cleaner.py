import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class DataCleaner:
    """Class for cleaning and validating market data"""
    
    def clean_exchange(self, exchange_data):
        """
        Clean and validate exchange data
        
        Args:
            exchange_data (dict): Raw exchange data
            
        Returns:
            dict: Cleaned exchange data
        """
        clean_data = {}
        
        try:
            # Required fields
            if 'code' not in exchange_data or not exchange_data['code']:
                raise ValueError("Exchange code is required")
            
            clean_data['code'] = exchange_data['code'].strip().upper()
            
            # Handle name
            if 'name' in exchange_data and exchange_data['name']:
                clean_data['name'] = exchange_data['name'].strip()
            else:
                clean_data['name'] = f"{clean_data['code']} Exchange"
            
            # Handle country
            if 'country' in exchange_data and exchange_data['country']:
                clean_data['country'] = exchange_data['country'].strip()
            else:
                clean_data['country'] = 'Unknown'
            
            # Handle website URL
            if 'website_url' in exchange_data and exchange_data['website_url']:
                clean_data['website_url'] = exchange_data['website_url'].strip()
            
            # Add optional fields that exist
            for field in ['description', 'timezone']:
                if field in exchange_data and exchange_data[field]:
                    clean_data[field] = exchange_data[field].strip()
            
        except Exception as e:
            logger.error(f"Error cleaning exchange data: {e}")
            raise
        
        return clean_data
    
    def clean_ticker(self, ticker_data):
        """
        Clean and validate ticker data
        
        Args:
            ticker_data (dict): Raw ticker data
            
        Returns:
            dict: Cleaned ticker data
        """
        clean_data = {}
        
        try:
            # Required fields
            if 'symbol' not in ticker_data or not ticker_data['symbol']:
                raise ValueError("Ticker symbol is required")
            
            if 'company_name' not in ticker_data or not ticker_data['company_name']:
                raise ValueError("Company name is required")
            
            if 'exchange_code' not in ticker_data or not ticker_data['exchange_code']:
                raise ValueError("Exchange code is required")
            
            # Clean and normalize fields
            clean_data['symbol'] = ticker_data['symbol'].strip().upper()
            clean_data['company_name'] = ticker_data['company_name'].strip()
            clean_data['exchange_code'] = ticker_data['exchange_code'].strip().upper()
            
            # Handle currency
            if 'currency' in ticker_data and ticker_data['currency']:
                clean_data['currency'] = ticker_data['currency'].strip().upper()
            else:
                # Default currency based on exchange
                exchange_currencies = {
                    'JSE': 'ZAR',
                    'NGX': 'NGN',
                    'BRVM': 'XOF'
                }
                clean_data['currency'] = exchange_currencies.get(clean_data['exchange_code'], 'USD')
            
            # Handle sector if present
            if 'sector' in ticker_data and ticker_data['sector']:
                clean_data['sector'] = ticker_data['sector'].strip()
            
            # Handle description if present
            if 'description' in ticker_data and ticker_data['description']:
                clean_data['description'] = ticker_data['description'].strip()
            
        except Exception as e:
            logger.error(f"Error cleaning ticker data: {e}")
            raise
        
        return clean_data
    
    def clean_price(self, price_data, ticker_symbol=None):
        """
        Clean and validate price data
        
        Args:
            price_data (dict): Raw price data
            ticker_symbol (str, optional): Ticker symbol for reference
            
        Returns:
            dict: Cleaned price data
        """
        clean_data = {}
        
        try:
            # Required fields
            if 'date' not in price_data:
                raise ValueError("Price date is required")
            
            if 'close_price' not in price_data or price_data['close_price'] is None:
                raise ValueError("Close price is required")
            
            # Clean date
            if isinstance(price_data['date'], str):
                try:
                    # Try different date formats
                    for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d %b %Y']:
                        try:
                            clean_data['date'] = datetime.strptime(price_data['date'], date_format).date()
                            break
                        except ValueError:
                            continue
                    
                    if 'date' not in clean_data:
                        raise ValueError(f"Unrecognized date format: {price_data['date']}")
                
                except Exception as e:
                    logger.error(f"Error parsing date {price_data['date']}: {e}")
                    raise
            else:
                clean_data['date'] = price_data['date']
            
            # Clean numeric values
            for field in ['open_price', 'high_price', 'low_price', 'close_price']:
                if field in price_data and price_data[field] is not None:
                    clean_data[field] = self._clean_numeric(price_data[field])
            
            # Clean volume
            if 'volume' in price_data and price_data['volume'] is not None:
                clean_data['volume'] = self._clean_integer(price_data['volume'])
            
            # Add ticker symbol if provided
            if ticker_symbol:
                clean_data['ticker_symbol'] = ticker_symbol.strip().upper()
            
        except Exception as e:
            ticker_info = f" for {ticker_symbol}" if ticker_symbol else ""
            logger.error(f"Error cleaning price data{ticker_info}: {e}")
            raise
        
        return clean_data
    
    def clean_index(self, index_data):
        """
        Clean and validate index data
        
        Args:
            index_data (dict): Raw index data
            
        Returns:
            dict: Cleaned index data
        """
        clean_data = {}
        
        try:
            # Required fields
            if 'symbol' not in index_data or not index_data['symbol']:
                raise ValueError("Index symbol is required")
            
            if 'name' not in index_data or not index_data['name']:
                raise ValueError("Index name is required")
            
            if 'exchange_code' not in index_data or not index_data['exchange_code']:
                raise ValueError("Exchange code is required")
            
            # Clean and normalize fields
            clean_data['symbol'] = index_data['symbol'].strip().upper()
            clean_data['name'] = index_data['name'].strip()
            clean_data['exchange_code'] = index_data['exchange_code'].strip().upper()
            
            # Handle description if present
            if 'description' in index_data and index_data['description']:
                clean_data['description'] = index_data['description'].strip()
            
        except Exception as e:
            logger.error(f"Error cleaning index data: {e}")
            raise
        
        return clean_data
    
    def clean_index_value(self, value_data, index_symbol=None):
        """
        Clean and validate index value data
        
        Args:
            value_data (dict): Raw index value data
            index_symbol (str, optional): Index symbol for reference
            
        Returns:
            dict: Cleaned index value data
        """
        clean_data = {}
        
        try:
            # Required fields
            if 'date' not in value_data:
                raise ValueError("Index value date is required")
            
            if 'value' not in value_data or value_data['value'] is None:
                raise ValueError("Index value is required")
            
            # Clean date
            if isinstance(value_data['date'], str):
                try:
                    # Try different date formats
                    for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d %b %Y']:
                        try:
                            clean_data['date'] = datetime.strptime(value_data['date'], date_format).date()
                            break
                        except ValueError:
                            continue
                    
                    if 'date' not in clean_data:
                        raise ValueError(f"Unrecognized date format: {value_data['date']}")
                
                except Exception as e:
                    logger.error(f"Error parsing date {value_data['date']}: {e}")
                    raise
            else:
                clean_data['date'] = value_data['date']
            
            # Clean value
            clean_data['value'] = self._clean_numeric(value_data['value'])
            
            # Clean change percent if present
            if 'change_percent' in value_data and value_data['change_percent'] is not None:
                clean_data['change_percent'] = self._clean_numeric(value_data['change_percent'])
            
            # Add index symbol if provided
            if index_symbol:
                clean_data['index_symbol'] = index_symbol.strip().upper()
            
        except Exception as e:
            index_info = f" for {index_symbol}" if index_symbol else ""
            logger.error(f"Error cleaning index value data{index_info}: {e}")
            raise
        
        return clean_data
    
    def _clean_numeric(self, value):
        """Clean and convert a value to a float"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols, commas, and other non-numeric characters
            clean_value = re.sub(r'[^\d.-]', '', value.strip())
            return float(clean_value) if clean_value else None
        
        return None
    
    def _clean_integer(self, value):
        """Clean and convert a value to an integer"""
        if isinstance(value, int):
            return value
        
        if isinstance(value, float):
            return int(value)
        
        if isinstance(value, str):
            # Remove commas and other non-numeric characters
            clean_value = re.sub(r'[^\d]', '', value.strip())
            return int(clean_value) if clean_value else None
        
        return None
