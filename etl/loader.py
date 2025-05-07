import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from models import Exchange, Stock, StockPrice, Index, IndexValue

logger = logging.getLogger(__name__)

class DataLoader:
    """Loads transformed data into the database."""
    
    def __init__(self, db_session):
        """
        Initialize the data loader.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
    
    def load_stocks(self, transformed_stocks, exchange_code):
        """
        Load transformed stock data into the database.
        
        Args:
            transformed_stocks (list): List of transformed stock dictionaries
            exchange_code (str): Exchange code
            
        Returns:
            int: Number of stocks processed
        """
        if not transformed_stocks:
            logger.warning(f"No stocks to load for {exchange_code}")
            return 0
        
        processed_count = 0
        
        try:
            # First, get or create the exchange record
            exchange = self._get_or_create_exchange(exchange_code)
            
            for stock_data in transformed_stocks:
                try:
                    # Look for an existing stock record
                    ticker = stock_data.get('ticker')
                    existing_stock = self.db_session.query(Stock).filter(
                        Stock.ticker == ticker,
                        Stock.exchange_id == exchange.id
                    ).first()
                    
                    if existing_stock:
                        # Update existing stock
                        existing_stock.name = stock_data.get('name')
                        existing_stock.sector = stock_data.get('sector')
                        existing_stock.currency = stock_data.get('currency')
                        existing_stock.last_updated = datetime.now()
                        logger.debug(f"Updated stock {ticker}")
                    else:
                        # Create new stock
                        new_stock = Stock(
                            ticker=ticker,
                            name=stock_data.get('name'),
                            sector=stock_data.get('sector'),
                            exchange_id=exchange.id,
                            currency=stock_data.get('currency'),
                            created_at=datetime.now(),
                            last_updated=datetime.now()
                        )
                        self.db_session.add(new_stock)
                        logger.debug(f"Created new stock {ticker}")
                    
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error loading stock {stock_data.get('ticker', 'unknown')}: {str(e)}")
                    continue
            
            self.db_session.commit()
            logger.info(f"Loaded {processed_count} stocks for {exchange_code}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading stocks for {exchange_code}: {str(e)}")
            self.db_session.rollback()
        except Exception as e:
            logger.error(f"Error loading stocks for {exchange_code}: {str(e)}")
            self.db_session.rollback()
        
        return processed_count
    
    def load_stock_prices(self, transformed_prices, exchange_code):
        """
        Load transformed stock price data into the database.
        
        Args:
            transformed_prices (list): List of transformed price dictionaries
            exchange_code (str): Exchange code
            
        Returns:
            int: Number of price points processed
        """
        if not transformed_prices:
            logger.warning(f"No stock prices to load for {exchange_code}")
            return 0
        
        processed_count = 0
        
        try:
            # Get the exchange record
            exchange = self.db_session.query(Exchange).filter_by(code=exchange_code).first()
            if not exchange:
                logger.error(f"Exchange {exchange_code} not found in database")
                return 0
            
            # Get all stocks for this exchange (to avoid repeated queries)
            stocks = {
                stock.ticker: stock.id 
                for stock in self.db_session.query(Stock).filter_by(exchange_id=exchange.id).all()
            }
            
            for price_data in transformed_prices:
                try:
                    ticker = price_data.get('ticker')
                    date_str = price_data.get('date')
                    
                    # Convert date string to date object
                    try:
                        price_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        logger.warning(f"Invalid date format {date_str} for {ticker}, skipping")
                        continue
                    
                    # Find the stock_id
                    stock_id = stocks.get(ticker)
                    if not stock_id:
                        logger.warning(f"Stock {ticker} not found in database, skipping price")
                        continue
                    
                    # Look for an existing price record
                    existing_price = self.db_session.query(StockPrice).filter(
                        StockPrice.stock_id == stock_id,
                        StockPrice.date == price_date
                    ).first()
                    
                    if existing_price:
                        # Update existing price
                        existing_price.close_price = price_data.get('close_price')
                        existing_price.open_price = price_data.get('open_price')
                        existing_price.high_price = price_data.get('high_price')
                        existing_price.low_price = price_data.get('low_price')
                        existing_price.volume = price_data.get('volume')
                        existing_price.change_percent = price_data.get('change_percent')
                        logger.debug(f"Updated price for {ticker} on {price_date}")
                    else:
                        # Create new price record
                        new_price = StockPrice(
                            stock_id=stock_id,
                            date=price_date,
                            close_price=price_data.get('close_price'),
                            open_price=price_data.get('open_price'),
                            high_price=price_data.get('high_price'),
                            low_price=price_data.get('low_price'),
                            volume=price_data.get('volume'),
                            change_percent=price_data.get('change_percent'),
                            created_at=datetime.now()
                        )
                        self.db_session.add(new_price)
                        logger.debug(f"Created new price for {ticker} on {price_date}")
                    
                    processed_count += 1
                    
                    # Commit in batches to avoid large transactions
                    if processed_count % 100 == 0:
                        self.db_session.commit()
                        
                except Exception as e:
                    logger.error(f"Error loading price for {price_data.get('ticker', 'unknown')}: {str(e)}")
                    continue
            
            self.db_session.commit()
            logger.info(f"Loaded {processed_count} price points for {exchange_code}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading prices for {exchange_code}: {str(e)}")
            self.db_session.rollback()
        except Exception as e:
            logger.error(f"Error loading prices for {exchange_code}: {str(e)}")
            self.db_session.rollback()
        
        return processed_count
    
    def load_indices(self, transformed_indices, transformed_values, exchange_code):
        """
        Load transformed index data into the database.
        
        Args:
            transformed_indices (list): List of transformed index dictionaries
            transformed_values (list): List of transformed index value dictionaries
            exchange_code (str): Exchange code
            
        Returns:
            int: Number of indices processed
        """
        if not transformed_indices:
            logger.warning(f"No indices to load for {exchange_code}")
            return 0
        
        processed_count = 0
        
        try:
            # Get the exchange record
            exchange = self.db_session.query(Exchange).filter_by(code=exchange_code).first()
            if not exchange:
                logger.error(f"Exchange {exchange_code} not found in database")
                return 0
            
            # Process indices
            index_id_map = {}  # To map index codes to their IDs
            
            for index_data in transformed_indices:
                try:
                    code = index_data.get('code')
                    
                    # Look for an existing index record
                    existing_index = self.db_session.query(Index).filter(
                        Index.code == code,
                        Index.exchange_id == exchange.id
                    ).first()
                    
                    if existing_index:
                        # Update existing index
                        existing_index.name = index_data.get('name')
                        existing_index.last_updated = datetime.now()
                        index_id_map[code] = existing_index.id
                        logger.debug(f"Updated index {code}")
                    else:
                        # Create new index
                        new_index = Index(
                            code=code,
                            name=index_data.get('name'),
                            exchange_id=exchange.id,
                            created_at=datetime.now(),
                            last_updated=datetime.now()
                        )
                        self.db_session.add(new_index)
                        self.db_session.flush()  # Need to flush to get the ID
                        index_id_map[code] = new_index.id
                        logger.debug(f"Created new index {code}")
                    
                    processed_count += 1
                except Exception as e:
                    logger.error(f"Error loading index {index_data.get('code', 'unknown')}: {str(e)}")
                    continue
            
            # Process index values
            for value_data in transformed_values:
                try:
                    index_code = value_data.get('index_code')
                    date_str = value_data.get('date')
                    
                    # Convert date string to date object
                    try:
                        value_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        logger.warning(f"Invalid date format {date_str} for index {index_code}, skipping")
                        continue
                    
                    # Find the index_id
                    index_id = index_id_map.get(index_code)
                    if not index_id:
                        logger.warning(f"Index {index_code} not found in database, skipping value")
                        continue
                    
                    # Look for an existing value record
                    existing_value = self.db_session.query(IndexValue).filter(
                        IndexValue.index_id == index_id,
                        IndexValue.date == value_date
                    ).first()
                    
                    if existing_value:
                        # Update existing value
                        existing_value.value = value_data.get('value')
                        existing_value.change_percent = value_data.get('change_percent')
                        logger.debug(f"Updated value for index {index_code} on {value_date}")
                    else:
                        # Create new value record
                        new_value = IndexValue(
                            index_id=index_id,
                            date=value_date,
                            value=value_data.get('value'),
                            change_percent=value_data.get('change_percent'),
                            created_at=datetime.now()
                        )
                        self.db_session.add(new_value)
                        logger.debug(f"Created new value for index {index_code} on {value_date}")
                except Exception as e:
                    logger.error(f"Error loading value for index {value_data.get('index_code', 'unknown')}: {str(e)}")
                    continue
            
            self.db_session.commit()
            logger.info(f"Loaded {processed_count} indices for {exchange_code}")
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading indices for {exchange_code}: {str(e)}")
            self.db_session.rollback()
        except Exception as e:
            logger.error(f"Error loading indices for {exchange_code}: {str(e)}")
            self.db_session.rollback()
        
        return processed_count
    
    def _get_or_create_exchange(self, exchange_code):
        """Get or create an exchange record."""
        from config import STOCK_EXCHANGES
        
        exchange = self.db_session.query(Exchange).filter_by(code=exchange_code).first()
        
        if not exchange:
            # Create a new exchange record
            exchange_info = STOCK_EXCHANGES.get(exchange_code, {})
            exchange = Exchange(
                code=exchange_code,
                name=exchange_info.get('name', f'{exchange_code} Exchange'),
                country=exchange_info.get('country', 'Africa'),
                currency=exchange_info.get('currency', 'Unknown'),
                website=exchange_info.get('url', ''),
                timezone=exchange_info.get('timezone', 'Africa/Johannesburg'),
                last_updated=datetime.now()
            )
            self.db_session.add(exchange)
            self.db_session.commit()
            logger.info(f"Created new exchange record for {exchange_code}")
        
        return exchange
