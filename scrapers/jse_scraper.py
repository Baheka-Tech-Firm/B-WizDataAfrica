import logging
import re
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import json
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class JSEScraper(BaseScraper):
    """Scraper for Johannesburg Stock Exchange (JSE)."""
    
    def __init__(self):
        super().__init__('https://www.jse.co.za', 'JSE')
        self.equity_url = 'https://www.jse.co.za/market-data/equity-market'
        self.price_data_url = 'https://www.jse.co.za/market-data/equity-market/price-data'
        self.indices_url = 'https://www.jse.co.za/market-data/indices'
    
    def scrape_stocks(self):
        """
        Scrape JSE stocks information.
        
        Returns:
            list: List of stock dictionaries
        """
        self.log_scrape_start()
        html = self.fetch_html(self.equity_url)
        if not html:
            logger.error("Failed to fetch JSE stocks data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        stocks = []
        
        try:
            # Look for the table containing stock listings
            stock_tables = soup.select('table.equity-table')
            
            if not stock_tables:
                logger.warning("No stock tables found on JSE page")
                return []
            
            for table in stock_tables:
                rows = table.select('tbody tr')
                
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 4:  # Ensure we have enough cells
                        try:
                            ticker = cells[0].get_text(strip=True)
                            name = cells[1].get_text(strip=True)
                            
                            # Some data cleaning
                            ticker = ticker.upper()
                            
                            stock = {
                                'ticker': ticker,
                                'name': name,
                                'exchange_code': 'JSE',
                                'currency': 'ZAR',
                                'last_updated': datetime.now().strftime('%Y-%m-%d')
                            }
                            
                            # Try to extract sector if available
                            if len(cells) > 4:
                                sector = cells[4].get_text(strip=True)
                                if sector:
                                    stock['sector'] = sector
                            
                            stocks.append(stock)
                        except Exception as e:
                            logger.error(f"Error parsing JSE stock row: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"Error scraping JSE stocks: {e}")
        
        self.log_scrape_complete('stocks', len(stocks))
        return stocks
    
    def scrape_stock_prices(self, ticker=None):
        """
        Scrape JSE stock prices.
        
        Args:
            ticker (str, optional): Specific JSE ticker to scrape prices for
            
        Returns:
            dict: Dictionary with tickers as keys and lists of price dictionaries as values
        """
        self.log_scrape_start()
        html = self.fetch_html(self.price_data_url)
        if not html:
            logger.error("Failed to fetch JSE price data")
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        price_data = {}
        
        try:
            # Look for price data tables or data in a structured format
            price_tables = soup.select('table.price-table')
            
            if not price_tables:
                logger.warning("No price tables found on JSE page")
                return {}
            
            for table in price_tables:
                # Extract table header to identify columns
                headers = [th.get_text(strip=True) for th in table.select('thead th')]
                
                # Create mappings for the columns we're interested in
                col_map = {
                    'ticker': next((i for i, h in enumerate(headers) if 'code' in h.lower() or 'ticker' in h.lower()), None),
                    'close': next((i for i, h in enumerate(headers) if 'close' in h.lower() or 'price' in h.lower()), None),
                    'open': next((i for i, h in enumerate(headers) if 'open' in h.lower()), None),
                    'high': next((i for i, h in enumerate(headers) if 'high' in h.lower()), None),
                    'low': next((i for i, h in enumerate(headers) if 'low' in h.lower()), None),
                    'volume': next((i for i, h in enumerate(headers) if 'volume' in h.lower()), None),
                    'change': next((i for i, h in enumerate(headers) if 'change' in h.lower() or '%' in h), None),
                    'date': next((i for i, h in enumerate(headers) if 'date' in h.lower()), None),
                }
                
                rows = table.select('tbody tr')
                today = datetime.now().strftime('%Y-%m-%d')
                
                for row in rows:
                    cells = row.select('td')
                    if len(cells) < max(filter(None, col_map.values())) + 1:
                        continue
                    
                    try:
                        row_ticker = cells[col_map['ticker']].get_text(strip=True).upper() if col_map['ticker'] is not None else None
                        
                        # Skip if we're looking for a specific ticker and this isn't it
                        if ticker and row_ticker != ticker.upper():
                            continue
                        
                        # Extract price data
                        price_info = {
                            'date': cells[col_map['date']].get_text(strip=True) if col_map['date'] is not None else today,
                            'close_price': self._extract_float(cells[col_map['close']].get_text(strip=True)) if col_map['close'] is not None else None,
                            'open_price': self._extract_float(cells[col_map['open']].get_text(strip=True)) if col_map['open'] is not None else None,
                            'high_price': self._extract_float(cells[col_map['high']].get_text(strip=True)) if col_map['high'] is not None else None,
                            'low_price': self._extract_float(cells[col_map['low']].get_text(strip=True)) if col_map['low'] is not None else None,
                            'volume': self._extract_int(cells[col_map['volume']].get_text(strip=True)) if col_map['volume'] is not None else None,
                            'change_percent': self._extract_float(cells[col_map['change']].get_text(strip=True)) if col_map['change'] is not None else None
                        }
                        
                        # Standardize date format
                        try:
                            date_obj = datetime.strptime(price_info['date'], '%d %b %Y')
                            price_info['date'] = date_obj.strftime('%Y-%m-%d')
                        except:
                            price_info['date'] = today
                        
                        if row_ticker not in price_data:
                            price_data[row_ticker] = []
                        
                        price_data[row_ticker].append(price_info)
                    except Exception as e:
                        logger.error(f"Error parsing JSE price row: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Error scraping JSE stock prices: {e}")
        
        count = sum(len(prices) for prices in price_data.values())
        self.log_scrape_complete('price points', count)
        return price_data
    
    def scrape_indices(self):
        """
        Scrape JSE indices information.
        
        Returns:
            list: List of index dictionaries
        """
        self.log_scrape_start()
        html = self.fetch_html(self.indices_url)
        if not html:
            logger.error("Failed to fetch JSE indices data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        indices = []
        
        try:
            # Look for indices tables
            index_tables = soup.select('table.indices-table')
            
            if not index_tables:
                logger.warning("No indices tables found on JSE page")
                return []
            
            for table in index_tables:
                rows = table.select('tbody tr')
                
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 3:  # Ensure we have enough cells
                        try:
                            code = cells[0].get_text(strip=True)
                            name = cells[1].get_text(strip=True)
                            value = self._extract_float(cells[2].get_text(strip=True))
                            
                            index = {
                                'code': code,
                                'name': name,
                                'exchange_code': 'JSE',
                                'last_updated': datetime.now().strftime('%Y-%m-%d'),
                                'value': value
                            }
                            
                            # Try to extract change if available
                            if len(cells) > 3:
                                change = self._extract_float(cells[3].get_text(strip=True))
                                if change is not None:
                                    index['change_percent'] = change
                            
                            indices.append(index)
                        except Exception as e:
                            logger.error(f"Error parsing JSE index row: {e}")
                            continue
        
        except Exception as e:
            logger.error(f"Error scraping JSE indices: {e}")
        
        self.log_scrape_complete('indices', len(indices))
        return indices
    
    def _extract_float(self, text):
        """Extract a float from text, handling common formats."""
        if not text or text.strip() in ('-', 'N/A'):
            return None
        
        # Remove currency symbols, commas and handle percentages
        text = re.sub(r'[R$€£¥]', '', text)
        text = text.replace(',', '')
        
        # Handle percentages
        if '%' in text:
            text = text.replace('%', '')
            try:
                return float(text)
            except ValueError:
                return None
                
        try:
            return float(text)
        except ValueError:
            return None
    
    def _extract_int(self, text):
        """Extract an integer from text, handling common formats."""
        if not text or text.strip() in ('-', 'N/A'):
            return None
        
        # Remove commas and spaces
        text = text.replace(',', '').replace(' ', '')
        
        # Handle K/M/B suffixes
        if 'K' in text:
            text = text.replace('K', '')
            try:
                return int(float(text) * 1000)
            except ValueError:
                return None
        elif 'M' in text:
            text = text.replace('M', '')
            try:
                return int(float(text) * 1000000)
            except ValueError:
                return None
        elif 'B' in text:
            text = text.replace('B', '')
            try:
                return int(float(text) * 1000000000)
            except ValueError:
                return None
        
        try:
            return int(text)
        except ValueError:
            try:
                return int(float(text))
            except ValueError:
                return None
