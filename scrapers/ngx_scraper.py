import logging
import re
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import json
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class NGXScraper(BaseScraper):
    """Scraper for Nigerian Exchange Group (NGX)."""
    
    def __init__(self):
        super().__init__('https://ngxgroup.com', 'NGX')
        self.equity_url = 'https://ngxgroup.com/exchange/data/equities-price-list/'
        self.market_summary_url = 'https://ngxgroup.com/exchange/data/market-summary/'
        self.indices_url = 'https://ngxgroup.com/exchange/data/indices/'
    
    def scrape_stocks(self):
        """
        Scrape NGX stocks information.
        
        Returns:
            list: List of stock dictionaries
        """
        self.log_scrape_start()
        html = self.fetch_html(self.equity_url)
        if not html:
            logger.error("Failed to fetch NGX stocks data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        stocks = []
        
        try:
            # NGX equity data is typically in a table with price list
            table = soup.select_one('table.price-list-table')
            
            if not table:
                logger.warning("No stock table found on NGX page")
                return []
            
            # Extract headers to identify columns
            headers = [th.get_text(strip=True).lower() for th in table.select('thead th')]
            
            # Create column index mapping
            col_map = {
                'ticker': next((i for i, h in enumerate(headers) if 'symbol' in h or 'ticker' in h), None),
                'name': next((i for i, h in enumerate(headers) if 'name' in h or 'company' in h), None),
                'sector': next((i for i, h in enumerate(headers) if 'sector' in h or 'industry' in h), None)
            }
            
            rows = table.select('tbody tr')
            
            for row in rows:
                cells = row.select('td')
                if len(cells) < max(filter(None, col_map.values())) + 1:
                    continue
                
                try:
                    ticker = cells[col_map['ticker']].get_text(strip=True) if col_map['ticker'] is not None else None
                    name = cells[col_map['name']].get_text(strip=True) if col_map['name'] is not None else None
                    sector = cells[col_map['sector']].get_text(strip=True) if col_map['sector'] is not None else None
                    
                    if not ticker or not name:
                        continue
                    
                    stock = {
                        'ticker': ticker.upper(),
                        'name': name,
                        'exchange_code': 'NGX',
                        'currency': 'NGN',
                        'last_updated': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    if sector:
                        stock['sector'] = sector
                    
                    stocks.append(stock)
                except Exception as e:
                    logger.error(f"Error parsing NGX stock row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping NGX stocks: {e}")
        
        self.log_scrape_complete('stocks', len(stocks))
        return stocks
    
    def scrape_stock_prices(self, ticker=None):
        """
        Scrape NGX stock prices.
        
        Args:
            ticker (str, optional): Specific NGX ticker to scrape prices for
            
        Returns:
            dict: Dictionary with tickers as keys and lists of price dictionaries as values
        """
        self.log_scrape_start()
        html = self.fetch_html(self.equity_url)
        if not html:
            logger.error("Failed to fetch NGX price data")
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        price_data = {}
        
        try:
            # NGX price data is typically in the same table as the equity list
            table = soup.select_one('table.price-list-table')
            
            if not table:
                logger.warning("No price table found on NGX page")
                return {}
            
            # Extract headers to identify columns
            headers = [th.get_text(strip=True).lower() for th in table.select('thead th')]
            
            # Create column index mapping
            col_map = {
                'ticker': next((i for i, h in enumerate(headers) if 'symbol' in h or 'ticker' in h), None),
                'close': next((i for i, h in enumerate(headers) if 'close' in h or 'closing' in h), None),
                'open': next((i for i, h in enumerate(headers) if 'open' in h or 'opening' in h), None),
                'high': next((i for i, h in enumerate(headers) if 'high' in h), None),
                'low': next((i for i, h in enumerate(headers) if 'low' in h), None),
                'volume': next((i for i, h in enumerate(headers) if 'volume' in h), None),
                'change': next((i for i, h in enumerate(headers) if 'change' in h or '%' in h), None)
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
                        'date': today,
                        'close_price': self._extract_float(cells[col_map['close']].get_text(strip=True)) if col_map['close'] is not None else None,
                        'open_price': self._extract_float(cells[col_map['open']].get_text(strip=True)) if col_map['open'] is not None else None,
                        'high_price': self._extract_float(cells[col_map['high']].get_text(strip=True)) if col_map['high'] is not None else None,
                        'low_price': self._extract_float(cells[col_map['low']].get_text(strip=True)) if col_map['low'] is not None else None,
                        'volume': self._extract_int(cells[col_map['volume']].get_text(strip=True)) if col_map['volume'] is not None else None,
                        'change_percent': self._extract_float(cells[col_map['change']].get_text(strip=True)) if col_map['change'] is not None else None
                    }
                    
                    if row_ticker not in price_data:
                        price_data[row_ticker] = []
                    
                    price_data[row_ticker].append(price_info)
                except Exception as e:
                    logger.error(f"Error parsing NGX price row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping NGX stock prices: {e}")
        
        count = sum(len(prices) for prices in price_data.values())
        self.log_scrape_complete('price points', count)
        return price_data
    
    def scrape_indices(self):
        """
        Scrape NGX indices information.
        
        Returns:
            list: List of index dictionaries
        """
        self.log_scrape_start()
        html = self.fetch_html(self.indices_url)
        if not html:
            logger.error("Failed to fetch NGX indices data")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        indices = []
        
        try:
            # NGX indices are typically in a dedicated table
            table = soup.select_one('table.indices-table')
            
            if not table:
                logger.warning("No indices table found on NGX page")
                return []
            
            # Extract headers to identify columns
            headers = [th.get_text(strip=True).lower() for th in table.select('thead th')]
            
            # Create column index mapping
            col_map = {
                'code': next((i for i, h in enumerate(headers) if 'code' in h or 'symbol' in h), None),
                'name': next((i for i, h in enumerate(headers) if 'name' in h or 'description' in h), None),
                'value': next((i for i, h in enumerate(headers) if 'value' in h or 'price' in h or 'close' in h), None),
                'change': next((i for i, h in enumerate(headers) if 'change' in h or '%' in h), None)
            }
            
            rows = table.select('tbody tr')
            
            for row in rows:
                cells = row.select('td')
                if len(cells) < max(filter(None, col_map.values())) + 1:
                    continue
                
                try:
                    code = cells[col_map['code']].get_text(strip=True) if col_map['code'] is not None else None
                    name = cells[col_map['name']].get_text(strip=True) if col_map['name'] is not None else None
                    value = self._extract_float(cells[col_map['value']].get_text(strip=True)) if col_map['value'] is not None else None
                    change = self._extract_float(cells[col_map['change']].get_text(strip=True)) if col_map['change'] is not None else None
                    
                    if not code or not name:
                        continue
                    
                    index = {
                        'code': code,
                        'name': name,
                        'exchange_code': 'NGX',
                        'last_updated': datetime.now().strftime('%Y-%m-%d'),
                        'value': value,
                        'change_percent': change
                    }
                    
                    indices.append(index)
                except Exception as e:
                    logger.error(f"Error parsing NGX index row: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping NGX indices: {e}")
        
        self.log_scrape_complete('indices', len(indices))
        return indices
    
    def _extract_float(self, text):
        """Extract a float from text, handling common formats."""
        if not text or text.strip() in ('-', 'N/A'):
            return None
        
        # Remove currency symbols, commas and handle percentages
        text = re.sub(r'[₦$€£¥]', '', text)
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
