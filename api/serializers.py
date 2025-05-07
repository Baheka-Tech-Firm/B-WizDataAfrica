def serialize_exchange(exchange):
    """Serialize an Exchange object to a dictionary."""
    return {
        'id': exchange.id,
        'code': exchange.code,
        'name': exchange.name,
        'country': exchange.country,
        'currency': exchange.currency,
        'website': exchange.website,
        'timezone': exchange.timezone,
        'description': exchange.description,
        'last_updated': exchange.last_updated.isoformat() if exchange.last_updated else None
    }

def serialize_stock(stock):
    """Serialize a Stock object to a dictionary."""
    return {
        'id': stock.id,
        'ticker': stock.ticker,
        'name': stock.name,
        'sector': stock.sector,
        'exchange': stock.exchange.code if stock.exchange else None,
        'currency': stock.currency,
        'description': stock.description,
        'website': stock.website,
        'market_cap': stock.market_cap,
        'outstanding_shares': stock.outstanding_shares,
        'last_updated': stock.last_updated.isoformat() if stock.last_updated else None
    }

def serialize_stock_price(price):
    """Serialize a StockPrice object to a dictionary."""
    return {
        'id': price.id,
        'date': price.date.isoformat(),
        'close_price': price.close_price,
        'open_price': price.open_price,
        'high_price': price.high_price,
        'low_price': price.low_price,
        'volume': price.volume,
        'change_percent': price.change_percent
    }

def serialize_index(index):
    """Serialize an Index object to a dictionary."""
    return {
        'id': index.id,
        'code': index.code,
        'name': index.name,
        'exchange': index.exchange.code if index.exchange else None,
        'description': index.description,
        'last_updated': index.last_updated.isoformat() if index.last_updated else None
    }

def serialize_index_value(value):
    """Serialize an IndexValue object to a dictionary."""
    return {
        'id': value.id,
        'date': value.date.isoformat(),
        'value': value.value,
        'change_percent': value.change_percent
    }

def serialize_macro_indicator(indicator):
    """Serialize a MacroIndicator object to a dictionary."""
    return {
        'id': indicator.id,
        'code': indicator.code,
        'name': indicator.name,
        'country': indicator.country,
        'category': indicator.category,
        'unit': indicator.unit,
        'description': indicator.description,
        'source': indicator.source
    }

def serialize_macro_value(value):
    """Serialize a MacroIndicatorValue object to a dictionary."""
    return {
        'id': value.id,
        'date': value.date.isoformat(),
        'value': value.value
    }

def serialize_market_summary(summary):
    """Serialize a MarketSummary object to a dictionary."""
    return {
        'id': summary.id,
        'title': summary.title,
        'date': summary.date.isoformat(),
        'content': summary.content,
        'highlights': summary.highlights,
        'created_at': summary.created_at.isoformat() if summary.created_at else None
    }
