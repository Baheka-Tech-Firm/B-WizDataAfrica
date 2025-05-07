import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models import MarketSummary, Exchange, Stock, StockPrice, Index, IndexValue

logger = logging.getLogger(__name__)

def generate_market_summary(db_session):
    """
    Generate a daily market summary.
    
    Args:
        db_session: SQLAlchemy database session
        
    Returns:
        MarketSummary: Created market summary object
    """
    logger.info("Generating daily market summary")
    
    # Get today's date and yesterday's date
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Check if we already have a summary for today
    existing_summary = db_session.query(MarketSummary).filter_by(date=today).first()
    if existing_summary:
        logger.info(f"Market summary for {today} already exists, updating")
        summary = existing_summary
    else:
        logger.info(f"Creating new market summary for {today}")
        summary = MarketSummary(
            title=f"African Markets Daily Summary - {today.strftime('%d %b %Y')}",
            date=today,
            content="",
            highlights="",
            created_at=datetime.now()
        )
        db_session.add(summary)
    
    try:
        # Generate content
        content = []
        highlights = []
        
        # Get exchanges
        exchanges = db_session.query(Exchange).all()
        
        for exchange in exchanges:
            exchange_content = []
            
            # Add exchange header
            exchange_content.append(f"## {exchange.name} ({exchange.code})")
            
            # Get index performance
            indices = db_session.query(Index).filter_by(exchange_id=exchange.id).all()
            if indices:
                exchange_content.append("\n### Key Indices")
                index_details = []
                
                for index in indices:
                    latest_value = db_session.query(IndexValue).filter_by(index_id=index.id).order_by(desc(IndexValue.date)).first()
                    if latest_value:
                        change_text = ""
                        if latest_value.change_percent is not None:
                            change_text = f"{'↑' if latest_value.change_percent > 0 else '↓'} {abs(latest_value.change_percent):.2f}%"
                            
                            # Add significant moves to highlights
                            if abs(latest_value.change_percent) > 1.5:
                                highlights.append(
                                    f"{index.name} ({exchange.code}) {'gained' if latest_value.change_percent > 0 else 'lost'} "
                                    f"{abs(latest_value.change_percent):.2f}%"
                                )
                        
                        index_details.append(f"- **{index.name}**: {latest_value.value:.2f} {change_text}")
                
                exchange_content.extend(index_details)
            
            # Get top gainers for this exchange
            top_gainers = (
                db_session.query(Stock, StockPrice)
                .join(StockPrice, Stock.id == StockPrice.stock_id)
                .filter(Stock.exchange_id == exchange.id, StockPrice.date == today)
                .filter(StockPrice.change_percent > 0)
                .order_by(desc(StockPrice.change_percent))
                .limit(5)
                .all()
            )
            
            if top_gainers:
                exchange_content.append("\n### Top Gainers")
                gainers_details = []
                
                for stock, price in top_gainers:
                    gainers_details.append(
                        f"- **{stock.ticker}** ({stock.name}): {price.close_price:.2f} {exchange.currency} "
                        f"↑ {price.change_percent:.2f}%"
                    )
                    
                    # Add significant gainers to highlights
                    if price.change_percent > 5:
                        highlights.append(
                            f"{stock.ticker} ({exchange.code}) gained {price.change_percent:.2f}%"
                        )
                
                exchange_content.extend(gainers_details)
            
            # Get top losers for this exchange
            top_losers = (
                db_session.query(Stock, StockPrice)
                .join(StockPrice, Stock.id == StockPrice.stock_id)
                .filter(Stock.exchange_id == exchange.id, StockPrice.date == today)
                .filter(StockPrice.change_percent < 0)
                .order_by(StockPrice.change_percent)
                .limit(5)
                .all()
            )
            
            if top_losers:
                exchange_content.append("\n### Top Losers")
                losers_details = []
                
                for stock, price in top_losers:
                    losers_details.append(
                        f"- **{stock.ticker}** ({stock.name}): {price.close_price:.2f} {exchange.currency} "
                        f"↓ {abs(price.change_percent):.2f}%"
                    )
                    
                    # Add significant losers to highlights
                    if price.change_percent < -5:
                        highlights.append(
                            f"{stock.ticker} ({exchange.code}) lost {abs(price.change_percent):.2f}%"
                        )
                
                exchange_content.extend(losers_details)
            
            # Get most active stocks by volume
            most_active = (
                db_session.query(Stock, StockPrice)
                .join(StockPrice, Stock.id == StockPrice.stock_id)
                .filter(Stock.exchange_id == exchange.id, StockPrice.date == today)
                .filter(StockPrice.volume > 0)
                .order_by(desc(StockPrice.volume))
                .limit(5)
                .all()
            )
            
            if most_active:
                exchange_content.append("\n### Most Active")
                active_details = []
                
                for stock, price in most_active:
                    active_details.append(
                        f"- **{stock.ticker}** ({stock.name}): {price.volume:,} shares, "
                        f"{price.close_price:.2f} {exchange.currency}"
                    )
                
                exchange_content.extend(active_details)
            
            # Add exchange summary to content
            content.append("\n".join(exchange_content))
        
        # Set summary content
        summary.content = "\n\n".join(content)
        
        # Set highlights (top 5)
        summary.highlights = "\n".join(highlights[:5]) if highlights else "No significant market moves today."
        
        # Save to database
        db_session.commit()
        logger.info(f"Market summary for {today} generated successfully")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating market summary: {str(e)}")
        db_session.rollback()
        raise
