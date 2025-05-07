import logging
import re
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import json
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class BRVMScraper(BaseScraper):
    """Scraper for Bourse Régionale des Valeurs Mobilières (BRVM)."""
    
    def __init__(self):
        super().__init__('https://www.brvm.org', 'BRVM')
        self.equity_url = 'https://www.brvm.org/en/cours-actions/0'
        self.indices_url = 'https://www.brvm.org/en/indices/0'
        self.market_summary_url = 'https://www.brvm.org/en/market-summary'
    
    def scrape_stocks(self):
        """
        Scrape BRVM stocks information.
        
        Returns:
            list: List of stock dictionaries
        """
        self.log_scrape_start()
        html = self.fetch_html(self.equity_url)
        if not html:
            logger.error("Failed to fetch BRVM stocks data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        stocks = []
        
        try:
            # BRVM stock data is typically in a table with a specific class
            table = soup.select_one('table.table-striped')
            
            if not table:
                logger.warning("No stock table found on BRVM page")
                return []
            
            # Extract headers to identify columns
            headers = [th.get_text(strip=True).lower() for th in table.select('thead th')]
            
            # Create column index mapping
            col_map = {
                'ticker': next((i for i, h in enumerate(headers) if 'symbol' in h or 'ticker' in h or 'code' in h), 0),
                'name': next((i for i, h in enumerate(headers) if 'name' in h or 'company' in h or 'title' in h), 1),
                'sector': next((i for i, h in enumerate(headers) if 'sector' in h or 'industry' in h), None)
            }
            
            rows = table.select('tbody tr')
            
            for row in rows:
                cells = row.select('td')
                if len(cells) < 2:  # Need at least ticker and name
                    continue
                
                try:
                    ticker = cells[col_map['ticker']].get_text(strip=True) if col_map['ticker'] is not None else None
                    name = cells[col_map['name']].get_text(strip=True) if col_map['name'] is not None else None
                    sector = cells[col_map['sector']].get_text(strip=True) if col_map['sector'] is not None and col_map['sector'] < len(cells) else None
                    
                    if not ticker or not name:
                        continue
                    
                    stock = {
                        'ticker': ticker.upper(),
                        'name': name,
                        'exchange_code': 'BRVM',
                        'currency': 'XOF',
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    if sector:
                        stock['sector'] = sector
                    
                    stocks.append(stock)
                except Exception as e:
                    logger.error(f"Error parsing BRVM stock row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping BRVM stocks: {e}")
        
        self.log_scrape_complete('stocks', len(stocks))
        return stocks
    
    def scrape_stock_prices(self, ticker=None):
        """
        Scrape BRVM stock prices.
        
        Args:
            ticker (str, optional): Specific BRVM ticker to scrape prices for
            
        Returns:
            dict: Dictionary with tickers as keys and lists of price dictionaries as values
        """
        self.log_scrape_start()
        html = self.fetch_html(self.equity_url)
        if not html:
            logger.error("Failed to fetch BRVM price data")
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        price_data = {}
        
        try:
            # BRVM price data is typically in the same table as the equity list
            table = soup.select_one('table.table-striped')
            
            if not table:
                logger.warning("No price table found on BRVM page")
                return {}
            
            # Extract headers to identify columns
            headers = [th.get_text(strip=True).lower() for th in table.select('thead th')]
            
            # Create column index mapping
            col_map = {
                'ticker': next((i for i, h in enumerate(headers) if 'symbol' in h or 'ticker' in h or 'code' in h), 0),
                'close': next((i for i, h in enumerate(headers) if 'close' in h or 'closing' in h or 'price' in h), 2),
                'open': next((i for i, h in enumerate(headers) if 'open' in h or 'opening' in h or 'previous' in h), 3),
                'high': next((i for i, h in enumerate(headers) if 'high' in h), None),
                'low': next((i for i, h in enumerate(headers) if 'low' in h), None),
                'volume': next((i for i, h in enumerate(headers) if 'volume' in h or 'qty' in h), 4),
                'change': next((i for i, h in enumerate(headers) if 'change' in h or 'var' in h or '%' in h), 5)
            }
            
            rows = table.select('tbody tr')
            today = datetime.now().strftime('%Y-%m-%d')
            
            for row in rows:
                cells = row.select('td')
                if len(cells) < 6:  # Need enough cells for the basic data
                    continue
                
                try:
                    row_ticker = cells[col_map['ticker']].get_text(strip=True).upper() if col_map['ticker'] is not None else None
                    
                    # Skip if we're looking for a specific ticker and this isn't it
                    if ticker and row_ticker != ticker.upper():
                        continue
                    
                    # Extract price data
                    price_info = {
                        'date': today,
                        'close_price': self._extract_float(cells[col_map['close']].get_text(strip=True)) if col_map['close'] is not None else None,
                        'open_price': self._extract_float(cells[col_map['open']].get_text(strip=True)) if col_map['open'] is not None else None,
                        'volume': self._extract_int(cells[col_map['volume']].get_text(strip=True)) if col_map['volume'] is not None else None,
                        'change_percent': self._extract_float(cells[col_map['change']].get_text(strip=True)) if col_map['change'] is not None else None
                    }
                    
                    # Add high/low if available
                    if col_map['high'] is not None and col_map['high'] < len(cells):
                        price_info['high_price'] = self._extract_float(cells[col_map['high']].get_text(strip=True))
                    
                    if col_map['low'] is not None and col_map['low'] < len(cells):
                        price_info['low_price'] = self._extract_float(cells[col_map['low']].get_text(strip=True))
                    
                    if row_ticker not in price_data:
                        price_data[row_ticker] = []
                    
                    price_data[row_ticker].append(price_info)
                except Exception as e:
                    logger.error(f"Error parsing BRVM price row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping BRVM stock prices: {e}")
        
        count = sum(len(prices) for prices in price_data.values())
        self.log_scrape_complete('price points', count)
        return price_data
    
    def scrape_indices(self):
        """
        Scrape BRVM indices information.
        
        Returns:
            list: List of index dictionaries
        """
        self.log_scrape_start()
        html = self.fetch_html(self.indices_url)
        if not html:
            logger.error("Failed to fetch BRVM indices data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        indices = []
        
        try:
            # BRVM indices are typically in a dedicated table
            table = soup.select_one('table.table-striped')
            
            if not table:
                logger.warning("No indices table found on BRVM page")
                return []
            
            # Extract headers to identify columns
            headers = [th.get_text(strip=True).lower() for th in table.select('thead th')]
            
            # Create column index mapping
            col_map = {
                'code': next((i for i, h in enumerate(headers) if 'code' in h or 'symbol' in h or 'name' in h), 0),
                'value': next((i for i, h in enumerate(headers) if 'value' in h or 'price' in h or 'close' in h or 'points' in h), 1),
                'change': next((i for i, h in enumerate(headers) if 'change' in h or 'var' in h or '%' in h), 2)
            }
            
            rows = table.select('tbody tr')
            
            for row in rows:
                cells = row.select('td')
                if len(cells) < 3:  # Need basic data
                    continue
                
                try:
                    code = cells[col_map['code']].get_text(strip=True) if col_map['code'] is not None else None
                    value = self._extract_float(cells[col_map['value']].get_text(strip=True)) if col_map['value'] is not None else None
                    change = self._extract_float(cells[col_map['change']].get_text(strip=True)) if col_map['change'] is not None else None
                    
                    if not code:
                        continue
                    
                    # For BRVM, sometimes the code is the full name
                    code_parts = code.split()
                    short_code = code_parts[0] if code_parts else code
                    
                    index = {
                        'code': short_code,
                        'name': code,  # Use full text as name
                        'exchange_code': 'BRVM',
                        'last_updated': datetime.now().strftime('%Y-%m-%d'),
                        'value': value,
                        'change_percent': change
                    }
                    
                    indices.append(index)
                except Exception as e:
                    logger.error(f"Error parsing BRVM index row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping BRVM indices: {e}")
        
        self.log_scrape_complete('indices', len(indices))
        return indices
    
    def _extract_float(self, text):
        """Extract a float from text, handling common formats."""
        if not text or text.strip() in ('-', 'N/A'):
            return None
        
        # Remove currency symbols, commas and handle percentages
        text = re.sub(r'[FCFA$€£¥]', '', text)
        text = text.replace(',', '').replace(' ', '')
        
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
