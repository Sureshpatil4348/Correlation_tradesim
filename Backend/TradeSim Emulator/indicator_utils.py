import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def calculate_rsi(symbol: str, period: int, timeframe: int) -> float:
    """
    Standardized RSI calculation for both live trading and websocket indicators.
    Parameters:
        symbol: Trading pair symbol
        period: RSI period
        timeframe: Trading timeframe in minutes (e.g., 1, 5, 15, 30, 60, 240, 1440)
    """
    try:
        # Map timeframe to MT5 constant
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1,
            240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1
        }
        mt5_timeframe = timeframe_map.get(timeframe)
        if mt5_timeframe is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None
            
        logger.info(f"Calculating RSI for {symbol} - Period: {period}, Timeframe: {timeframe} minutes")
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, period + 1)
        if rates is None:
            logger.error(f"Failed to get data for {symbol}")
            return None
            
        prices = pd.Series([rate['close'] for rate in rates])
        delta = prices.diff()
        
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        final_rsi = float(rsi.iloc[-1]) if not np.isnan(rsi.iloc[-1]) else None
        logger.info(f"RSI result for {symbol}: {final_rsi}")
        return final_rsi
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
        return None

def calculate_correlation(pair1: str, pair2: str, window: int, timeframe: int) -> float:
    """
    Standardized correlation calculation for both live trading and websocket indicators.
    Parameters:
        pair1: First trading pair symbol
        pair2: Second trading pair symbol
        window: Correlation window period
        timeframe: Trading timeframe in minutes (e.g., 1, 5, 15, 30, 60, 240, 1440)
    """
    try:
        # Map timeframe to MT5 constant
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1,
            240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1
        }
        mt5_timeframe = timeframe_map.get(timeframe)
        if mt5_timeframe is None:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None
            
        logger.info(f"Calculating correlation between {pair1} and {pair2} - Window: {window}, Timeframe: {timeframe} minutes")
        rates1 = mt5.copy_rates_from_pos(pair1, mt5_timeframe, 0, window + 1)
        rates2 = mt5.copy_rates_from_pos(pair2, mt5_timeframe, 0, window + 1)
        
        if rates1 is None or rates2 is None:
            logger.error(f"Failed to get data for {pair1} or {pair2}")
            return None
            
        prices1 = pd.Series([rate['close'] for rate in rates1])
        prices2 = pd.Series([rate['close'] for rate in rates2])
        
        correlation = prices1.rolling(window=window).corr(prices2).iloc[-1]
        final_correlation = float(correlation) if not np.isnan(correlation) else None
        logger.info(f"Correlation result: {final_correlation}")
        return final_correlation
        
    except Exception as e:
        logger.error(f"Error calculating correlation: {e}")
        return None

def get_tick_data(symbol: str) -> dict:
    """
    Standardized tick data retrieval for both systems.
    """
    try:
        ticks = mt5.copy_ticks_from(
            symbol,
            datetime.now() - timedelta(seconds=10),
            100,
            mt5.COPY_TICKS_ALL
        )
        
        if ticks is not None and len(ticks) > 0:
            last_tick = ticks[-1]
            return {
                "bid": float(last_tick[1]),
                "ask": float(last_tick[2]),
                "time": datetime.fromtimestamp(last_tick[5] / 1000)
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting tick data for {symbol}: {e}")
        return None 