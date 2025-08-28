"""Database connection and session management."""

from typing import Generator
import os
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

Base = declarative_base()

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL", 
            "postgresql://postgres:postgres@127.0.0.1:5432/options_bot"
        )
        self.engine: Engine | None = None
        self.SessionLocal: sessionmaker | None = None
        
    def initialize(self) -> None:
        """Initialize database engine and session factory."""
        try:
            self.engine = create_engine(self.database_url, echo=False)
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            logger.info(f"Database connection initialized: {self.database_url}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session with automatic cleanup."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized. Call initialize() first.")
            
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def session_context(self):
        """Get a context manager for database sessions."""
        from contextlib import contextmanager
        
        @contextmanager
        def _session_context():
            if not self.SessionLocal:
                raise RuntimeError("Database not initialized. Call initialize() first.")
                
            session = self.SessionLocal()
            try:
                yield session
            except Exception as e:
                session.rollback()
                logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                session.close()
        
        return _session_context()
    
    async def get_latest_market_screening(self):
        """Get latest market data from database as fallback."""
        from typing import Dict, Any
        
        with self.session_context() as session:
            try:
                # Get latest market data for each symbol
                symbols = ['MSFT', 'GOOGL', 'AMD', 'AMZN']
                stock_analysis = {}
                
                for symbol in symbols:
                    # Get most recent market data
                    market_query = """
                        SELECT * FROM market_data 
                        WHERE symbol = :symbol 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """
                    market_result = session.execute(text(market_query), {'symbol': symbol}).fetchone()
                    
                    # Get most recent technical indicators  
                    tech_query = """
                        SELECT * FROM technical_indicators 
                        WHERE symbol = :symbol 
                        ORDER BY timestamp DESC 
                        LIMIT 1
                    """
                    tech_result = session.execute(text(tech_query), {'symbol': symbol}).fetchone()
                    
                    if market_result:
                        # Create analysis object from database data
                        stock_analysis[symbol] = {
                            'current_price': market_result.current_price,
                            'momentum_score': 0.5,  # Default neutral
                            'setup_quality': 'fair',  # Default
                            'trend_direction': 'neutral',  # Default
                            'key_levels': f"Support: ${float(market_result.current_price)-5:.2f}, Resistance: ${float(market_result.current_price)+8:.2f}",
                            'volume_profile': f"{market_result.volume_ratio or 1.0:.1f}x average",
                            'pattern': 'database_fallback',
                            'indicators': {
                                'rsi': tech_result.rsi if tech_result else 50.0,
                                'ema_20': tech_result.ema_20 if tech_result else market_result.current_price,
                                'ema_50': tech_result.ema_50 if tech_result else market_result.current_price
                            }
                        }
                    else:
                        # If no database data, create minimal fallback
                        base_prices = {"MSFT": 420.0, "GOOGL": 180.0, "AMD": 140.0, "AMZN": 185.0}
                        price = base_prices[symbol]
                        stock_analysis[symbol] = {
                            'current_price': price,
                            'momentum_score': 0.5,
                            'setup_quality': 'weak',
                            'trend_direction': 'neutral',
                            'key_levels': f"Support: ${price-5:.2f}, Resistance: ${price+8:.2f}",
                            'volume_profile': "1.0x average",
                            'pattern': 'no_data_fallback',
                            'indicators': {'rsi': 50.0, 'ema_20': price, 'ema_50': price}
                        }
                
                # Return screening structure matching what agents expect
                return {
                    'timestamp': session.execute(text("SELECT NOW()")).scalar(),
                    'symbols': symbols,
                    'selected_target': 'MSFT',  # Default target
                    'selection_reasoning': "Database fallback - latest available data",
                    'stock_analysis': stock_analysis,
                    'technical_data': {symbol: {'rsi': analysis['indicators']['rsi']} for symbol, analysis in stock_analysis.items()},
                    'status': 'database_fallback'
                }
                
            except Exception as e:
                logger.error(f"Failed to get latest market data from database: {str(e)}")
                # Return absolute minimal fallback if database fails
                return {
                    'timestamp': None,
                    'symbols': ['MSFT'],
                    'selected_target': 'MSFT',
                    'selection_reasoning': "Database error - minimal fallback",
                    'stock_analysis': {'MSFT': {'current_price': 420.0, 'momentum_score': 0.5}},
                    'technical_data': {'MSFT': {'rsi': 50.0}},
                    'status': 'error_fallback'
                }

    def close(self) -> None:
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()