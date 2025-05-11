from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, field_validator, Field
import MetaTrader5 as mt5
import pandas as pd
import time
import asyncio
import numpy as np
import time
from datetime import datetime, timedelta
import pytz
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
import base64
from fastapi.responses import StreamingResponse
from typing import Dict, List, Tuple, Optional, Union
from io import BytesIO
from typing import Optional
import logging
from functools import lru_cache
from collections import defaultdict
from indicator_utils import calculate_rsi, calculate_correlation, get_tick_data

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Update app initialization
app = FastAPI(
    title="MT5 Trading API",
    middleware=[
        Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    ]
)

# Add rate limit error handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class MT5LoginRequest(BaseModel):
    account: int
    password: str
    server: str

# Pydantic model for request body
class BacktestRequest(BaseModel):
    id: int
    name: str
    currencyPairs: List[str]
    lotSize: List[str]
    timeFrame: Union[str, int]
    analysisTimeframe: Union[str, int] = None
    magicNumber: str
    tradeComment: str
    rsiPeriod: int
    correlationWindow: int
    rsiOverbought: float
    rsiOversold: float
    entryThreshold: float
    exitThreshold: float
    startDate: datetime
    endDate: datetime
    cooldownPeriod: float = 24.0
    startingBalance: float = Field(gt=0)  # Changed from initial_balance to startingBalance

    @field_validator('currencyPairs')
    @classmethod
    def validate_currency_pairs(cls, v):
        if len(v) != 2:
            raise ValueError('Must provide exactly 2 currency pairs')
        return v

    @field_validator('lotSize')
    @classmethod
    def validate_lot_sizes(cls, v):
        if len(v) != 2:
            raise ValueError('Must provide exactly 2 lot sizes')
        try:
            lots = [float(size) for size in v]
            if any(lot <= 0 for lot in lots):
                raise ValueError('Lot sizes must be greater than 0')
            return v
        except ValueError:
            raise ValueError('Lot sizes must be valid numbers')

    @field_validator('timeFrame', 'analysisTimeframe')
    @classmethod
    def validate_timeframes(cls, v):
        if v is None:
            return v
        valid_timeframes = [1, 5, 15, 30, 60, 240, 1440]
        timeframe = int(v) if isinstance(v, str) else v
        if timeframe not in valid_timeframes:
            raise ValueError(f'Timeframe must be one of {valid_timeframes}')
        return timeframe

    @field_validator('rsiPeriod', 'correlationWindow')
    @classmethod
    def validate_periods(cls, v):
        if v <= 0:
            raise ValueError('Period must be positive')
        return v

    @field_validator('rsiOverbought', 'rsiOversold')
    @classmethod
    def validate_rsi_levels(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('RSI levels must be between 0 and 100')
        return v

    @field_validator('entryThreshold')
    @classmethod
    def validate_entry_threshold(cls, v):
        if not -1 <= v <= 1:
            raise ValueError('Entry threshold must be between -1 and 1')
        return v

    @field_validator('exitThreshold')
    @classmethod
    def validate_exit_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Exit threshold must be between 0 and 1')
        return v

    @field_validator('startDate', 'endDate')
    @classmethod
    def validate_dates(cls, v):
        if not isinstance(v, datetime):
            raise ValueError('Date must be a datetime object')
        return v

    @field_validator('startingBalance')  # Updated validator name
    @classmethod
    def validate_starting_balance(cls, v):
        if v <= 0:
            raise ValueError('Starting balance must be greater than 0')
        return v

    model_config = {
        'arbitrary_types_allowed': True
    }

class IndicatorRequest(BaseModel):
    id: int
    name: str
    currencyPairs: list[str]
    lotSize: list[str]
    timeFrame: int
    magicNumber: str
    tradeComment: str
    rsiPeriod: int
    correlationWindow: int
    rsiOverbought: float
    rsiOversold: float
    entryThreshold: float
    exitThreshold: float
    startingBalance: float
    status: str

    @field_validator('timeFrame')
    def validate_timeframe(cls, v):
        valid_timeframes = [1, 5, 15, 30, 60, 240, 1440]
        if v not in valid_timeframes:
            raise ValueError(f'Timeframe must be one of {valid_timeframes}')
        return v

    @field_validator('rsiPeriod')
    def validate_rsi_period(cls, v):
        if v <= 0:
            raise ValueError('RSI period must be positive')
        return v

    @field_validator('rsiOverbought', 'rsiOversold')
    def validate_rsi_levels(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('RSI levels must be between 0 and 100')
        return v

    @field_validator('entryThreshold', 'exitThreshold')
    def validate_correlation_thresholds(cls, v):
        if not -1 <= v <= 1:
            raise ValueError('Correlation thresholds must be between -1 and 1')
        return v

    @field_validator('currencyPairs')
    def validate_currency_pairs(cls, v):
        if len(v) != 2:
            raise ValueError('Exactly two currency pairs must be provided')
        return v

# Pydantic model for response
class TradeLog(BaseModel):
    entry_time: datetime
    exit_time: datetime
    long_pair: str
    short_pair: str
    long_entry_price: float
    long_exit_price: float
    short_entry_price: float
    short_exit_price: float
    total_profit: float

class PerformanceMetrics(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_profit_percentage: float
    net_profit_dollars: float
    max_drawdown_percentage: float
    max_drawdown_dollars: float
    sharpe_ratio: float
    avg_trade_duration: float
    profit_factor: float
    peak_balance: float
    final_balance: float

class EquityCurveData(BaseModel):
    date: str  # Ensure the date is a string
    equity: float
    
    

class BacktestResponse(BaseModel):
    trades: List[TradeLog]
    metrics: PerformanceMetrics
    correlation_vs_profit_plot: Optional[str] = None
    equity_curve_plot: Optional[str] = None
    equity_curve_data: Optional[List[EquityCurveData]] = None
    correlation_timeline_plot: Optional[str] = None

logged_in_user = None
active_strategies = {}
strategy_monitors = {}  # New dict to track monitoring state

def get_active_trades():
    if not mt5.initialize():
        return {"error": "Failes to intialise MT5"}
    
    orders = mt5.orders_get();
    active_orders = [order._asdict() for order in orders] if orders else []

    positions = mt5.positions_get()
    active_positions = [pos._asdict() for pos in positions] if positions else []

    return {"orders" : active_orders, "positions": active_positions}
    

def get_account_info():
    if not mt5.initialize():
        return {"error": "Failes to intialise MT5"}
    
    account_info = mt5.account_info()._asdict()
    return account_info


def get_trade_history():
    if not mt5.initialize():
        return {"error": "Failed to initialize MT5"}
    
    from_date = datetime.now().timestamp() - (30 * 24 * 60 * 60)
    to_date = datetime.now().timestamp()

    history = mt5.history_deals_get(from_date, to_date)
    positions = mt5.history_orders_get(from_date, to_date)
    
    trade_history = [deal._asdict() for deal in history if deal.type != 2] if history else []
    position_history = [pos._asdict() for pos in positions] if positions else []

    # Create a dictionary to group trades by position ID
    trades_by_position = {}
    
    # Group trades by their position ID
    for trade in trade_history:
        position_id = trade.get('position_id')
        if position_id not in trades_by_position:
            trades_by_position[position_id] = []
        trades_by_position[position_id].append(trade)

    combined_history = []
    
    # Match positions with their corresponding trades
    for position in position_history:
        position_id = position.get('ticket')
        related_trades = trades_by_position.get(position_id, [])
        
        combined_entry = {
            "position": position,
            "trades": related_trades
        }
        combined_history.append(combined_entry)

    # Add any remaining trades that don't have a matching position
    for position_id, trades in trades_by_position.items():
        # Fix the any() check to safely handle None positions
        if not any(
            entry.get('position') is not None and 
            entry['position'].get('ticket') == position_id 
            for entry in combined_history
        ):
            combined_entry = {
                "position": None,
                "trades": trades
            }
            combined_history.append(combined_entry)

    return combined_history

def get_user_login_status():
    mt5.initialize()
    if not mt5.initialize():
        return {"status": "error", "message": "Failed to initialize MT5"}

    account_info = mt5.account_info()
    if account_info is None:
        return {"status": "not_logged_in", "message": "User is not logged in"}

    return {
        "status": "logged_in",
        "account": account_info.login,
        "balance": account_info.balance,
        "equity": account_info.equity
    }

# Function to place a trade
def place_trade(symbol, lot, order_type, magic_number, comment=None):
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logger.error(f"Failed to get tick data for {symbol}")
        return None
    
    price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(f"Failed to get symbol info for {symbol}")
        return None
        
    filling_types = [
        mt5.ORDER_FILLING_FOK,
        mt5.ORDER_FILLING_IOC,
        mt5.ORDER_FILLING_RETURN
    ]
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "magic": magic_number,
        "deviation": 10,
        "comment": comment if comment else "Auto-Trader",
        "type_time": mt5.ORDER_TIME_GTC
    }
    
    for filling_type in filling_types:
        request["type_filling"] = filling_type
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return result
    
    return None

# Backtesting Engine (same as before)
class PairedTradingBacktester:
    def __init__(self, request: BacktestRequest):
        self.pair1 = request.currencyPairs[0]
        self.pair2 = request.currencyPairs[1]
        self.timeframe = int(request.timeFrame)
        self.analysis_timeframe = int(request.analysisTimeframe) if request.analysisTimeframe else self.timeframe
        self.start_date = request.startDate
        self.end_date = request.endDate
        self.correlation_window = request.correlationWindow
        self.rsi_window = request.rsiPeriod
        self.rsi_overbought = request.rsiOverbought
        self.rsi_oversold = request.rsiOversold
        self.correlation_entry_threshold = request.entryThreshold
        self.correlation_exit_threshold = request.exitThreshold
        self.lot_size_pair1 = float(request.lotSize[0])
        self.lot_size_pair2 = float(request.lotSize[1])
        self.cooldown_period = request.cooldownPeriod
        self.magic_number = int(request.magicNumber)
        self.trade_comment = request.tradeComment
        self.initial_balance = request.startingBalance
        print(f"Initial Balance: ${self.initial_balance:,.2f}")

        print(f"\nStrategy Parameters:")
        print(f"Pairs: {self.pair1} / {self.pair2}")
        print(f"Trading Timeframe: {self.timeframe} minutes")
        print(f"Analysis Timeframe: {self.analysis_timeframe} minutes")
        print(f"RSI Window: {self.rsi_window}")
        print(f"Correlation Window: {self.correlation_window}")
        print(f"Entry Threshold: {self.correlation_entry_threshold}")
        print(f"Exit Threshold: {self.correlation_exit_threshold}")
        print(f"RSI Levels - Overbought: {self.rsi_overbought}, Oversold: {self.rsi_oversold}")
        print(f"Lot Sizes - {self.pair1}: {self.lot_size_pair1}, {self.pair2}: {self.lot_size_pair2}")
        print(f"Cooldown Period: {self.cooldown_period} hours")

        self.active_trades = []
        self.last_entry_time = None
        self.trades = []
        
        self.data = self._load_data_from_mt5()
        self._validate_data()
        self.indicators = self._calculate_indicators()
    
    def _load_data_from_mt5(self) -> Dict[str, pd.DataFrame]:
        if not connection_manager.ensure_connection():
            raise ValueError("MT5 initialization failed!")

        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1,
            240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1
        }
        
        timeframe_mt5 = timeframe_map.get(int(self.timeframe))
        if timeframe_mt5 is None:
            raise ValueError(f"Invalid timeframe: {self.timeframe}")

        CHUNK_SIZE = 10000
        data = {}

        for pair in [self.pair1, self.pair2]:
            chunks = []
            current_date = self.start_date
            
            while current_date < self.end_date:
                chunk_end = min(current_date + timedelta(minutes=self.timeframe * CHUNK_SIZE), 
                              self.end_date)
                
                rates = mt5.copy_rates_range(pair, timeframe_mt5, current_date, chunk_end)
                
                if rates is None:
                    raise ValueError(f"Failed to fetch data for {pair}")
                    
                chunk_df = pd.DataFrame(rates)
                chunk_df['time'] = pd.to_datetime(chunk_df['time'], unit='s')
                chunks.append(chunk_df)
                
                current_date = chunk_end
                
            data[pair] = pd.concat(chunks)
            data[pair].set_index('time', inplace=True)
        
        return data
    
    def _calculate_indicators(self) -> Dict[str, pd.Series]:
        """
        Calculate indicators for the strategy.
        """
        pair1_df = self.data[self.pair1]
        pair2_df = self.data[self.pair2]
        
        # Convert windows to integers and create the rolling window
        correlation_window = str(self.correlation_window)
        rsi_window = str(self.rsi_window)
        
        # Calculate rolling correlation using numeric window
        rolling_corr = pair1_df['close'].rolling(window=int(correlation_window)).corr(pair2_df['close'])
        
        # Calculate RSI using numeric window
        pair1_rsi = self._calculate_rsi(pair1_df['close'], int(rsi_window))
        pair2_rsi = self._calculate_rsi(pair2_df['close'], int(rsi_window))
        
        # Align all series to have the same index
        common_index = rolling_corr.dropna().index.intersection(pair1_rsi.dropna().index).intersection(pair2_rsi.dropna().index)
        
        if len(common_index) == 0:
            raise ValueError(f"No common data points after indicator calculation. Try using a smaller window size than {self.correlation_window} or extending your date range.")
        
        rolling_corr = rolling_corr.loc[common_index]
        pair1_rsi = pair1_rsi.loc[common_index]
        pair2_rsi = pair2_rsi.loc[common_index]
        
        return {
            'rolling_correlation': rolling_corr,
            f'{self.pair1}_rsi': pair1_rsi,
            f'{self.pair2}_rsi': pair2_rsi
        }

    def calculate_performance_metrics(self) -> Dict[str, float]:
        """
        Calculate performance metrics using actual profit/loss values.
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'net_profit_percentage': 0.0,
                'net_profit_dollars': 0.0,
                'max_drawdown_percentage': 0.0,
                'max_drawdown_dollars': 0.0,
                'sharpe_ratio': 0.0,
                'avg_trade_duration': 0.0,
                'profit_factor': 0.0,
                'peak_balance': self.initial_balance,
                'final_balance': self.initial_balance
            }
        
        # Initialize tracking variables
        current_balance = self.initial_balance
        peak_balance = self.initial_balance
        max_drawdown_dollars = 0
        max_drawdown_percentage = 0
        winning_trades = 0
        losing_trades = 0
        total_profit = 0
        total_loss = 0
        
        # Process each trade
        trade_returns = []
        for trade in self.trades:
            # Get the actual profit in dollars
            long_profit = trade.get('long_profit', 0)  # These will be actual dollar values now
            short_profit = trade.get('short_profit', 0)
            trade_profit = long_profit + short_profit
            
            # Track wins/losses
            if trade_profit > 0:
                winning_trades += 1
                total_profit += trade_profit
            else:
                losing_trades += 1
                total_loss += abs(trade_profit)
            
            # Update current balance
            current_balance += trade_profit
            
            # Update peak balance and drawdown
            peak_balance = max(peak_balance, current_balance)
            if current_balance < peak_balance:
                drawdown_dollars = peak_balance - current_balance
                drawdown_percentage = (drawdown_dollars / peak_balance) * 100
                max_drawdown_dollars = max(max_drawdown_dollars, drawdown_dollars)
                max_drawdown_percentage = max(max_drawdown_percentage, drawdown_percentage)
            
            # Store return for Sharpe ratio calculation
            trade_returns.append(trade_profit)
        
        # Calculate final metrics
        total_trades = len(self.trades)
        win_rate = (winning_trades / total_trades) if total_trades > 0 else 0
        net_profit_dollars = total_profit - total_loss
        net_profit_percentage = (net_profit_dollars / self.initial_balance) * 100
        
        # Calculate Sharpe Ratio using actual returns
        if len(trade_returns) > 1:
            returns_series = pd.Series(trade_returns)
            sharpe_ratio = np.sqrt(252) * (returns_series.mean() / returns_series.std())
        else:
            sharpe_ratio = 0.0
        
        # Calculate profit factor
        profit_factor = total_profit / abs(total_loss) if total_loss != 0 else 999999.0  # Use a large number instead of infinity
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'net_profit_percentage': net_profit_percentage,
            'net_profit_dollars': net_profit_dollars,
            'max_drawdown_percentage': max_drawdown_percentage,
            'max_drawdown_dollars': max_drawdown_dollars,
            'sharpe_ratio': float(0.0) if np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio) else float(sharpe_ratio),
            'avg_trade_duration': float(np.mean([(trade['exit_time'] - trade['entry_time']).total_seconds() / 3600 for trade in self.trades])),
            'profit_factor': profit_factor,
            'peak_balance': peak_balance,
            'final_balance': current_balance
        }
    
    def _calculate_rsi(self, prices: pd.Series, window: int) -> pd.Series:
        """
        Calculate RSI for a given price series.
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def run_backtest(self) -> Dict[str, Union[List[Dict], Dict[str, float]]]:
        # Get the correct length to iterate over
        indicators_length = min(
            len(self.indicators['rolling_correlation']),
            len(self.indicators[f'{self.pair1}_rsi']),
            len(self.indicators[f'{self.pair2}_rsi'])
        )
        
        # Use this length rather than just one indicator's length
        index = self.indicators['rolling_correlation'].index[:indicators_length]
        print(f"Total periods to analyze: {len(index)}")

        for i in range(len(index)):
            current_time = index[i]

            # Check and exit existing trades
            trades_to_exit = self._check_exit_conditions(i)
            for trade_idx in sorted(trades_to_exit, reverse=True):
                self._exit_trade(i, trade_idx)

            # Check for new trade entry
            entry_condition, trade_direction = self._check_entry_conditions(i)
            if entry_condition:
                self._enter_trade(i, trade_direction)

        # Close any remaining trades at the end
        final_index = len(index) - 1
        while self.active_trades:
            self._exit_trade(final_index, 0)
        
        print(f"\nBacktest completed. Total trades: {len(self.trades)}")
        
        return {
            'trades': self.trades,
            'metrics': self.calculate_performance_metrics(),
        }

    def _check_entry_conditions(self, i: int) -> Tuple[bool, Optional[Dict[str, str]]]:
        # Make sure i is valid for all indicators
        indicators_length = min(
            len(self.indicators['rolling_correlation']),
            len(self.indicators[f'{self.pair1}_rsi']),
            len(self.indicators[f'{self.pair2}_rsi'])
        )
        
        if i >= indicators_length:
            return False, None
        
        current_time = self.indicators['rolling_correlation'].index[i]
        rolling_corr = self.indicators['rolling_correlation'].iloc[i]
        pair1_rsi = self.indicators[f'{self.pair1}_rsi'].iloc[i]
        pair2_rsi = self.indicators[f'{self.pair2}_rsi'].iloc[i]
        
        if self.last_entry_time is not None:
            hours_since_last_entry = (current_time - self.last_entry_time).total_seconds() / 3600
            if hours_since_last_entry < self.cooldown_period:
                return False, None
        
        if rolling_corr > self.correlation_entry_threshold:
            return False, None

        both_overbought = pair1_rsi > self.rsi_overbought and pair2_rsi > self.rsi_overbought
        both_oversold = pair1_rsi < self.rsi_oversold and pair2_rsi < self.rsi_oversold
        
        if both_overbought or both_oversold:
            return False, None
        
        if pair1_rsi > self.rsi_overbought and pair2_rsi < self.rsi_oversold:
            return True, {
                'long': self.pair2,
                'short': self.pair1,
                'long_lot': self.lot_size_pair2,
                'short_lot': self.lot_size_pair1
            }

        if pair1_rsi < self.rsi_oversold and pair2_rsi > self.rsi_overbought:
            return True, {
                'long': self.pair1,
                'short': self.pair2,
                'long_lot': self.lot_size_pair1,
                'short_lot': self.lot_size_pair2
            }
        
        return False, None

    def _check_exit_conditions(self, i: int) -> List[int]:
        if not self.active_trades:
            return []
        
        rolling_corr = self.indicators['rolling_correlation'].iloc[i]
        current_time = self.indicators['rolling_correlation'].index[i]
        trades_to_exit = []
        
        if rolling_corr > self.correlation_exit_threshold:            
            for idx, trade in enumerate(self.active_trades):
                total_profit = self._calculate_combined_profit(trade, current_time)
                
                if total_profit > 0:
                    trades_to_exit.append(idx)
        
        return trades_to_exit

    def _calculate_combined_profit(self, trade: Dict, current_time: datetime) -> float:
        long_profit = self._calculate_position_profit(
            trade['long_pair'],
            trade['long_entry_price'],
            current_time,
            trade['long_lot'],
            is_long=True
        )
        
        short_profit = self._calculate_position_profit(
            trade['short_pair'],
            trade['short_entry_price'],
            current_time,
            trade['short_lot'],
            is_long=False
        )
        
        return long_profit + short_profit

    def _calculate_position_profit(self, pair: str, entry_price: float, current_time: datetime, lot_size: float, is_long: bool) -> float:
        """
        Calculate profit for a single position using proper pip value calculations.
        """
        try:
            current_data = self.data[pair][self.data[pair].index == current_time]
            if current_data.empty:
                return 0.0
            
            current_price = current_data['close'].iloc[0]
            
            # Define pip size based on pair
            pip_size = 0.01 if pair.endswith('JPY') else 0.0001
            
            # Calculate price difference and convert to pips
            price_diff = current_price - entry_price if is_long else entry_price - current_price
            pips = price_diff / pip_size
            
            # Calculate pip value
            # Standard lot (1.0) = $10 per pip for most pairs
            # Mini lot (0.1) = $1 per pip
            # Micro lot (0.01) = $0.10 per pip
            standard_pip_value = 10.0
            if pair.endswith('JPY'):
                standard_pip_value = 10.0  # JPY pairs also use $10 per pip for standard lot
                
            # Calculate actual profit based on lot size
            pip_value = standard_pip_value * lot_size
            profit = pips * pip_value
            
            return profit
            
        except Exception as e:
            logger.error(f"Error calculating position profit: {e}")
            return 0.0

    def plot_correlation_vs_profit(self) -> str:
        """
        Generate a correlation vs profit plot and return it as a base64-encoded image.
        
        Returns:
        --------
        str
            Base64-encoded image of the plot.
        """
        
        # Extract correlation and profit data
        correlations = [trade['entry_correlation'] for trade in self.trades]
        profits = [trade['total_profit'] * 100 for trade in self.trades]  # Convert to percentage
        
        # Create scatter plot
        plt.figure(figsize=(12, 6))
        plt.scatter(correlations, profits, alpha=0.6)
        plt.title('Entry Correlation vs Trade Profit')
        plt.xlabel('Entry Correlation')
        plt.ylabel('Profit (%)')
        plt.grid(True)
        
        # Add horizontal line at y=0
        plt.axhline(y=0, color='r', linestyle='--', alpha=0.3)
        
        # Save the plot to a BytesIO object
        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        
        # Encode the image as base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        return image_base64

    def _enter_trade(self, i: int, trade_direction: Dict[str, str]) -> None:
        """
        Enter a new trade with proper lot size handling.
        """
        try:
            timestamp = self.indicators['rolling_correlation'].index[i]
            long_pair = trade_direction['long']
            short_pair = trade_direction['short']
            long_lot = trade_direction['long_lot']
            short_lot = trade_direction['short_lot']
            
            # Get entry prices
            long_data = self.data[long_pair][self.data[long_pair].index == timestamp]
            short_data = self.data[short_pair][self.data[short_pair].index == timestamp]
            
            if long_data.empty or short_data.empty:
                raise ValueError(f"No data found for timestamp: {timestamp}")
            
            long_price = long_data['close'].iloc[0]
            short_price = short_data['close'].iloc[0]
            
            # Create trade data with lot sizes
            trade_data = {
                'entry_time': timestamp,
                'long_pair': long_pair,
                'short_pair': short_pair,
                'long_entry_price': long_price,
                'short_entry_price': short_price,
                'long_lot': long_lot,
                'short_lot': short_lot,
                'entry_correlation': self.indicators['rolling_correlation'].iloc[i],
                'entry_long_rsi': self.indicators[f"{long_pair}_rsi"].iloc[i],
                'entry_short_rsi': self.indicators[f"{short_pair}_rsi"].iloc[i]
            }
            
            self.active_trades.append(trade_data)
            self.last_entry_time = timestamp
        
        except Exception as e:
            print(f"Error entering trade: {e}")

    def _exit_trade(self, i: int, trade_index: int) -> None:
        """
        Exit a trade with proper profit calculations.
        """
        try:
            trade_data = self.active_trades[trade_index]
            timestamp = self.indicators['rolling_correlation'].index[i]
            
            # Get exit prices
            long_data = self.data[trade_data['long_pair']][self.data[trade_data['long_pair']].index == timestamp]
            short_data = self.data[trade_data['short_pair']][self.data[trade_data['short_pair']].index == timestamp]
            
            if long_data.empty or short_data.empty:
                raise ValueError(f"No data found for timestamp: {timestamp}")
            
            long_exit_price = long_data['close'].iloc[0]
            short_exit_price = short_data['close'].iloc[0]
            
            # Calculate profits using lot sizes
            long_profit = self._calculate_position_profit(
                trade_data['long_pair'],
                trade_data['long_entry_price'],
                timestamp,
                trade_data['long_lot'],
                is_long=True
            )
            
            short_profit = self._calculate_position_profit(
                trade_data['short_pair'],
                trade_data['short_entry_price'],
                timestamp,
                trade_data['short_lot'],
                is_long=False
            )
            
            # Total profit in dollars
            total_profit = long_profit + short_profit
            
            # Update trade data
            trade_data.update({
                'exit_time': timestamp,
                'long_exit_price': long_exit_price,
                'short_exit_price': short_exit_price,
                'exit_correlation': self.indicators['rolling_correlation'].iloc[i],
                'exit_long_rsi': self.indicators[f"{trade_data['long_pair']}_rsi"].iloc[i],
                'exit_short_rsi': self.indicators[f"{trade_data['short_pair']}_rsi"].iloc[i],
                'trade_duration': (timestamp - trade_data['entry_time']).total_seconds() / 3600,
                'long_profit': long_profit,  # Actual dollar profit
                'short_profit': short_profit,  # Actual dollar profit
                'total_profit': total_profit  # Actual dollar profit
            })
            
            self.trades.append(trade_data.copy())
            self.active_trades.pop(trade_index)
        
        except Exception as e:
            logger.error(f"Error in _exit_trade: {e}")

    def _calculate_pips(self, entry_price: float, exit_price: float, pair: str) -> float:
        """
        Calculate the number of pips between entry and exit prices.
        
        Parameters:
        -----------
        entry_price : float
            Entry price of the trade
        exit_price : float
            Exit price of the trade
        pair : str
            Currency pair symbol (e.g., 'EURUSD', 'USDJPY')
            
        Returns:
        --------
        float
            Number of pips gained/lost
        """
        # For JPY pairs, 1 pip = 0.01, for others 1 pip = 0.0001
        pip_value = 0.01 if pair.endswith('JPY') else 0.0001
        return (exit_price - entry_price) / pip_value

    def plot_equity_curve(self, metrics: Dict[str, float]) -> Dict[str, Union[str, dict]]:
        if not self.trades:
            print("No trades to plot.")
            return {
                "plot_base64": None,
                "csv_data": None,
            }
        
        try:
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), height_ratios=[1, 1])
            
            # Extract trade data
            dates = [trade['exit_time'] for trade in self.trades]
            profits_percentage = [trade['total_profit'] * 100 for trade in self.trades]
            profits_dollars = [self.initial_balance * trade['total_profit'] for trade in self.trades]
            
            # Calculate cumulative equity curves
            equity_percentage = np.cumsum(profits_percentage)
            equity_dollars = self.initial_balance + np.cumsum(profits_dollars)
            
            # Plot percentage returns
            ax1.plot(dates, equity_percentage, label='Equity Curve (%)')
            ax1.set_title(f'Equity Curve - Percentage (Net: {metrics["net_profit_percentage"]:.2f}%)')
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Return (%)')
            ax1.grid(True)
            ax1.legend()
            
            # Plot dollar returns
            ax2.plot(dates, equity_dollars, label='Equity Curve ($)', color='green')
            ax2.set_title(f'Equity Curve - Dollars (Net: ${metrics["net_profit_dollars"]:,.2f})')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Account Balance ($)')
            ax2.grid(True)
            ax2.legend()
            
            # Format dates
            fig.autofmt_xdate()
            plt.tight_layout()
            
            # Save the plot
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            buf.seek(0)
            
            # Encode the image
            plot_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            # Prepare CSV data with the correct structure
            csv_data = [
                {
                    'date': str(date),
                    'equity': float(equity)  # Make sure equity is a float
                }
                for date, equity in zip(dates, equity_dollars)
            ]
            
            return {
                "plot_base64": plot_base64,
                "csv_data": csv_data,
            }
        
        except Exception as e:
            print(f"Error generating equity curve: {e}")
            return {
                "plot_base64": None,
                "csv_data": None,
            }

    def _validate_data(self):
        """
        Validate that we have enough data for analysis
        """
        if len(self.data[self.pair1]) < self.correlation_window:
            raise ValueError(f"Not enough data for {self.pair1}. Need at least {self.correlation_window} periods")
        if len(self.data[self.pair2]) < self.correlation_window:
            raise ValueError(f"Not enough data for {self.pair2}. Need at least {self.correlation_window} periods")
        
        print(f"Data validation passed. Available periods:")
        print(f"{self.pair1}: {len(self.data[self.pair1])} periods")
        print(f"{self.pair2}: {len(self.data[self.pair2])} periods")

    def plot_correlation_timeline(self) -> str:
        """
        Generate a plot showing correlation values over time and return it as a base64-encoded image.
        """
        try:
            # Get correlation data
            correlation_series = self.indicators['rolling_correlation']
            
            # Create figure with appropriate size
            plt.figure(figsize=(15, 7))
            
            # Plot correlation line
            plt.plot(correlation_series.index, correlation_series.values, 
                    label='Correlation', color='blue', linewidth=1)
            
            # Add entry and exit threshold lines
            plt.axhline(y=self.correlation_entry_threshold, color='r', 
                       linestyle='--', label=f'Entry Threshold ({self.correlation_entry_threshold})')
            plt.axhline(y=self.correlation_exit_threshold, color='g', 
                       linestyle='--', label=f'Exit Threshold ({self.correlation_exit_threshold})')
            
            # Add trade entry and exit points if there are trades
            for trade in self.trades:
                plt.scatter(trade['entry_time'], trade['entry_correlation'], 
                          color='green', marker='^', s=100, label='Trade Entry' if trade == self.trades[0] else "")
                plt.scatter(trade['exit_time'], trade['exit_correlation'], 
                          color='red', marker='v', s=100, label='Trade Exit' if trade == self.trades[0] else "")
            
            # Customize the plot
            plt.title(f'Correlation Timeline: {self.pair1} vs {self.pair2}')
            plt.xlabel('Date')
            plt.ylabel('Correlation')
            plt.grid(True, alpha=0.3)
            plt.legend()
            
            # Format x-axis dates
            plt.gcf().autofmt_xdate()
            
            # Add correlation bands
            plt.axhspan(-1, -0.7, alpha=0.1, color='red', label='Strong Negative')
            plt.axhspan(-0.7, -0.3, alpha=0.1, color='yellow', label='Moderate Negative')
            plt.axhspan(-0.3, 0.3, alpha=0.1, color='gray', label='Weak Correlation')
            plt.axhspan(0.3, 0.7, alpha=0.1, color='yellow', label='Moderate Positive')
            plt.axhspan(0.7, 1, alpha=0.1, color='green', label='Strong Positive')
            
            # Save the plot to a BytesIO object
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            buf.seek(0)
            
            # Encode the image as base64
            image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return image_base64
            
        except Exception as e:
            print(f"Error generating correlation timeline plot: {e}")
            return None

class RateLimiter:
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        
    def _clean_old_requests(self, endpoint: str, window: int):
        current_time = time.time()
        self._requests[endpoint] = [
            req_time for req_time in self._requests[endpoint]
            if current_time - req_time < window
        ]
    
    async def check_rate_limit(self, request: Request, max_requests: int, window: int) -> None:
        """
        Check if request is within rate limit
        
        Args:
            request: FastAPI request object
            max_requests: Maximum number of requests allowed in window
            window: Time window in seconds
        """
        endpoint = request.url.path
        self._clean_old_requests(endpoint, window)
        
        if len(self._requests[endpoint]) >= max_requests:
            oldest_request = self._requests[endpoint][0]
            wait_time = window - (time.time() - oldest_request)
            if wait_time > 0:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Please wait {wait_time:.1f} seconds"
                )
        
        self._requests[endpoint].append(time.time())

# Create global rate limiter instance
rate_limiter = RateLimiter()

@app.post("/mt5/login")
@limiter.limit("5/minute")
async def login_mt5(request: Request, login_request: MT5LoginRequest):
    # Rate limit: 5 requests per minute
    await rate_limiter.check_rate_limit(request, max_requests=5, window=60)
    
    # Log the incoming request
    print(f"Attempting login with account: {login_request.account}, server: {login_request.server}")

    # Initialize MetaTrader 5
    if not mt5.initialize():
        error = mt5.last_error()
        print(f"Error during MT5 initialization: {error}")  # Log the error
        raise HTTPException(status_code=500, detail=f"Failed to initialize MetaTrader 5: {error}")

    # Attempt to login
    if not mt5.login(login_request.account, password=login_request.password, server=login_request.server):
        error = mt5.last_error()
        print(f"MetaTrader5 login failed: {error}")  # Log the exact error for debugging
        raise HTTPException(status_code=401, detail=f"Login failed: {error}")

    # Retrieve account information
    account_info = mt5.account_info()

    # Check if account information is valid
    if account_info is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve account information")

    # Extract necessary account details
    account_data = {
        "balance": account_info.balance,
        "equity": account_info.equity,
        "margin": account_info.margin,
        "free_margin": account_info.margin_free,
        "currency": account_info.currency,
        "leverage": account_info.leverage,
        "account_number": account_info.login,
        "name": account_info.name
    }

    # Return account information
    return {"status": "success", "message": "Logged in successfully", "account_info": account_data}

@app.get("/mt5/status")
async def get_status():
    return get_user_login_status()

@app.get("/mt5/active-strategies")
async def get_active_strategies():
    print("Current active strategies:", active_strategies)  # Add debug print
    return {"active_strategies": list(active_strategies.keys())}

@app.get("/mt5/history")
async def get_history():
    return get_trade_history()

@app.get("/mt5/account")
async def get_account():
    return get_account_info()

@app.get("/mt5/trades")
async def get_trades():
    return get_active_trades()

@app.post("/mt5/start-strategy")
async def start_strategy(params: dict):
    strategy_id = params["id"]
    magic_number = int(params["magicNumber"])

    try:
        print(f"Starting strategy {strategy_id}")

        if strategy_id in active_strategies:
            print(f"strategy {strategy_id} is already running, stopping it")
            await stop_strategy_internal(strategy_id)

        monitor = StrategyMonitor(strategy_id, params)
        await monitor.initialize()

        active_strategies[strategy_id] = True
        strategy_monitors[strategy_id] = monitor
        
        # Save state after updating

        asyncio.create_task(monitor.monitor_trades())

        return {
            "status": "success",
            "message": f"Strategy {strategy_id} started/restarted",
            "existing_trades": len(monitor.monitored_trades),
            "activeTrades": len(active_strategies),
            "activeStrategies": active_strategies,
            "monitor": monitor
        }

    except Exception as e:
        print(f"Error starting strategy: {e}")
        if strategy_id in active_strategies:
            active_strategies.pop(strategy_id)
        if strategy_id in strategy_monitors:
            strategy_monitors.pop(strategy_id)
        return {"status": "error", "message": str(e)}

@app.post("/mt5/stop-strategy")
async def stop_strategy(params: dict):
    strategy_id = params["id"]

    try:
        if strategy_id not in active_strategies:
            return {
                "status": "error",
                "message": "Strategy not running"
            }

        monitor = strategy_monitors.get(strategy_id)
        if not monitor:
            return {
                "status": "error",
                "message": "Strategy monitor not found"
            }

        result = await monitor.stop(close_trades=True)
        
        active_strategies[strategy_id] = False
        active_strategies.pop(strategy_id, None)
        strategy_monitors.pop(strategy_id, None)

        return {
            "status": "stopped",
            "message": f"Strategy {strategy_id} stopped",
            **result
        }

    except Exception as e:
        print(f"Error stopping strategy: {e}")
        return {"status": "error", "message": str(e)}

async def stop_strategy_internal(strategy_id: str):
    """Internal function to stop strategy and clean up"""
    if strategy_id not in active_strategies:
        return {"message": "Strategy not running"}

    monitor = strategy_monitors.get(strategy_id)
    if monitor:
        result = await monitor.stop(close_trades=False)
        active_strategies[strategy_id] = False
        active_strategies.pop(strategy_id)
        strategy_monitors.pop(strategy_id)
        return result
    return {"message": "No monitor found"}

@app.post("/mt5/backtest-strategy")
@limiter.limit("3/minute")
async def backtest_strategy_endpoint(request: Request, backtest_request: BacktestRequest):
    # Rate limit: 3 requests per minute
    await rate_limiter.check_rate_limit(request, max_requests=3, window=60)
    
    if not connection_manager.ensure_connection():
        raise HTTPException(status_code=500, detail="Failed to initialize MT5")
        
    try:
        backtester = PairedTradingBacktester(backtest_request)
        results = backtester.run_backtest()
    
        plot_base64 = backtester.plot_correlation_vs_profit()
        equity_curve_result = backtester.plot_equity_curve(results['metrics'])
        correlation_timeline = backtester.plot_correlation_timeline()
        
        trades = [TradeLog(**trade) for trade in results['trades']]
        metrics = PerformanceMetrics(**results['metrics'])
    
        return BacktestResponse(
        trades=trades, 
        metrics=metrics, 
        correlation_vs_profit_plot=plot_base64,
        equity_curve_plot=equity_curve_result["plot_base64"],
        equity_curve_data=equity_curve_result["csv_data"],
        correlation_timeline_plot=correlation_timeline
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def close_position(ticket):
    """Close a specific position by ticket number."""
    position = mt5.positions_get(ticket=ticket)
    if not position:
        return False
    
    position = position[0]
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": mt5.ORDER_TYPE_BUY if position.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
        "position": position.ticket,
        "magic": position.magic,
        "comment": "Exit Strategy",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    return result.retcode == mt5.TRADE_RETCODE_DONE

class StrategyMonitor:
    def __init__(self, strategy_id, params):
        self.strategy_id = strategy_id
        self.params = params
        self.monitored_trades = []
        self.is_stopping = False
        self.last_trade_time = None
        self.cooldown_period = timedelta(hours=float(params.get("cooldownPeriod", 24)))
        self.magic_number = int(params["magicNumber"])
        self.timeframe = int(params["timeFrame"])
        self.trade_lock = asyncio.Lock()  # Lock for trade placement
        self.placing_trades = False  # Flag to track trade placement status
        
    async def initialize(self):
        """Initialize strategy monitoring and load existing trades"""
        if not mt5.initialize():
            raise Exception("Failed to initialize MT5")

        # Get all positions and filter manually to be sure
        all_positions = mt5.positions_get()
        if all_positions is None:
            print(f"No active positions found")
            return
            
        print(f"Total active positions in MT5: {len(all_positions)}")
        
        # Filter positions by magic number manually
        existing_trades = []
        for position in all_positions:
            if position.magic == self.magic_number:
                existing_trades.append(position)
        
        if existing_trades:
            print(f"\nFound {len(existing_trades)} existing trades for strategy {self.strategy_id} with magic number {self.magic_number}")
            
            # Find the most recent trade by comparing open times
            latest_trade_time = None
            for trade in existing_trades:
                self.monitored_trades.append(trade)
                print(f"Loaded existing trade: {trade.symbol} {trade.volume} lots, opened at {trade.time}, magic: {trade.magic}")
                
                # Convert MT5 time (which is typically in seconds since epoch) to datetime
                trade_time = datetime.fromtimestamp(trade.time)
                
                # Track the most recent trade time
                if latest_trade_time is None or trade_time > latest_trade_time:
                    latest_trade_time = trade_time
            
            # If we found trades, set the last trade time to the most recent one
            if latest_trade_time is not None:
                print(f"Setting last trade time to {latest_trade_time} based on existing trades")
                self.last_trade_time = latest_trade_time
                
                # Calculate and display remaining cooldown time if applicable
                time_since_last = datetime.now() - self.last_trade_time
                cooldown_remaining = self.cooldown_period - time_since_last
                if cooldown_remaining.total_seconds() > 0:
                    hours_remaining = cooldown_remaining.total_seconds() / 3600
                    print(f"Cooldown in effect: {hours_remaining:.1f} hours remaining before new trades can be placed")
                else:
                    print("Cooldown period has elapsed. New trades can be placed when conditions are met.")
        else:
            print(f"No existing trades found for strategy {self.strategy_id} with magic number {self.magic_number}")

    async def _check_exit_conditions(self):
        """Check and handle exit conditions for existing trades"""
        if not self.monitored_trades:
            return

        pair1, pair2 = self.params["currencyPairs"]
        correlation = calculate_correlation(pair1, pair2, int(self.params["correlationWindow"]), self.timeframe)

        if correlation is None or correlation <= float(self.params["exitThreshold"]):
            return
        
        pair1_trade = next((t for t in self.monitored_trades if t.symbol == pair1), None)
        pair2_trade = next((t for t in self.monitored_trades if t.symbol == pair2), None)

        if pair1_trade and pair2_trade:
            total_profit = pair1_trade.profit + pair2_trade.profit
            if total_profit > 0:
                print(f"Exiting both trades: Correlation = {correlation:.3f}, Total Profit = ${total_profit:.2f}")
                await self._close_position(pair1_trade)
                await self._close_position(pair2_trade)
            else:
                print(f"Holding trades: Correlation high but pair not profitable (${total_profit:.2f})")

    async def monitor_trades(self):
        """Main trade monitoring loop"""
        while active_strategies.get(self.strategy_id) and not self.is_stopping:
            try:
                # Update the list of monitored trades first
                await self._update_monitored_trades()
                
                # Check if existing trades should be closed
                await self._check_exit_conditions()
                
                # Only check for new entries if not already placing trades and cooldown has passed
                if not self.placing_trades:
                    # Check if lock is already held
                    if self.trade_lock.locked():
                        print(f"Trade lock is active, skipping entry check")
                    else:
                        # Check cooldown before trying to acquire lock
                        cooldown_active = (self.last_trade_time is not None and 
                                          datetime.now() - self.last_trade_time < self.cooldown_period)
                        
                        if not cooldown_active:
                            # Try to acquire lock for trade placement
                            try:
                                await asyncio.wait_for(self.trade_lock.acquire(), timeout=0.5)
                                try:
                                    self.placing_trades = True
                                    await self._check_entry_conditions()
                                finally:
                                    self.placing_trades = False
                                    self.trade_lock.release()
                            except asyncio.TimeoutError:
                                print("Timeout while waiting for trade lock, will try again later")
                        else:
                            # Only log occasionally to avoid spam
                            time_since_last = datetime.now() - self.last_trade_time
                            cooldown_remaining = self.cooldown_period - time_since_last
                            hours_remaining = cooldown_remaining.total_seconds() / 3600
                            if int(hours_remaining) % 4 == 0:  # Log every 4 hours
                                print(f"Skipping entry check: Cooldown in effect. {hours_remaining:.1f} hours remaining.")
                
                # Print current status
                await self._print_status()
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                # Make sure to reset flags and release lock if there's an exception
                self.placing_trades = False
                if self.trade_lock.locked():
                    try:
                        self.trade_lock.release()
                    except RuntimeError:
                        pass  # Ignore if lock was not acquired by this task
                
                if not active_strategies.get(self.strategy_id):
                    break
            
            # Sleep for a while before next iteration
            await asyncio.sleep(1)

    async def _update_monitored_trades(self):
        """Update status of monitored trades"""
        # Get all positions
        all_positions = mt5.positions_get()
        if all_positions is None:
            all_positions = []
        
        # Filter by magic number
        current_trades = [pos for pos in all_positions if pos.magic == self.magic_number]
        
        # Extract tickets for comparison
        current_tickets = set(trade.ticket for trade in current_trades)
        monitored_tickets = set(trade.ticket for trade in self.monitored_trades)
        
        # Find new and removed tickets
        new_tickets = current_tickets - monitored_tickets
        removed_tickets = monitored_tickets - current_tickets
        
        # Log changes
        if new_tickets:
            print(f"Strategy {self.strategy_id}: Found {len(new_tickets)} new trades to monitor")
        
        if removed_tickets:
            print(f"Strategy {self.strategy_id}: Removing {len(removed_tickets)} trades no longer active")
        
        # Add new trades to monitored list
        for trade in current_trades:
            if trade.ticket in new_tickets:
                self.monitored_trades.append(trade)
                print(f"Added new trade to monitoring: Ticket {trade.ticket}, Symbol {trade.symbol}, "
                      f"Type {'Buy' if trade.type == mt5.ORDER_TYPE_BUY else 'Sell'}, Magic {trade.magic}")
        
        # Remove trades that no longer exist
        self.monitored_trades = [trade for trade in self.monitored_trades if trade.ticket in current_tickets]

    async def _check_entry_conditions(self):
        """Check and handle entry conditions for new trades"""
        # Skip entry if stopping or already have trades
        if self.is_stopping or self.monitored_trades:
            return
        
        # Double-check cooldown period - defensive programming
        if (self.last_trade_time and 
            datetime.now() - self.last_trade_time < self.cooldown_period):
            return
        
        # Calculate indicators to decide on trade entry
        pair1, pair2 = self.params["currencyPairs"]
        correlation = calculate_correlation(
            pair1, 
            pair2, 
            int(self.params["correlationWindow"]),
            self.timeframe
        )

        if correlation is None or correlation >= float(self.params["entryThreshold"]):
            return

        rsi1 = calculate_rsi(
            pair1, 
            int(self.params["rsiPeriod"]),
            self.timeframe
        )
        rsi2 = calculate_rsi(
            pair2, 
            int(self.params["rsiPeriod"]),
            self.timeframe
        )

        if rsi1 is None or rsi2 is None:
            return

        if self._check_rsi_conditions(rsi1, rsi2):
            # CRITICAL: Set last_trade_time BEFORE attempting to place trades
            # This prevents another check from running while trade placement is in progress
            original_last_trade_time = self.last_trade_time
            self.last_trade_time = datetime.now()
            print(f"Setting last_trade_time to {self.last_trade_time} BEFORE trade placement")
            
            try:
                success = False
                if rsi1 > float(self.params["rsiOverbought"]) and rsi2 < float(self.params["rsiOversold"]):
                    success = await self._place_trades(pair1, pair2, is_first_pair_long=False, 
                                                     comment=self.params["tradeComment"])
                else:
                    success = await self._place_trades(pair1, pair2, is_first_pair_long=True,
                                                     comment=self.params["tradeComment"])
                
                if not success:
                    # Reset last_trade_time if trade placement failed
                    print("Trade placement failed, resetting last_trade_time")
                    self.last_trade_time = original_last_trade_time
            except Exception as e:
                # Reset last_trade_time on any exception
                print(f"Exception during trade placement: {e}, resetting last_trade_time")
                self.last_trade_time = original_last_trade_time
                raise  # Re-raise to allow the caller to handle it

    async def _place_trades(self, pair1, pair2, is_first_pair_long=True, comment=None):
        """Place a pair of trades based on the direction"""
        try:
            lot1 = float(self.params["lotSize"][0])
            lot2 = float(self.params["lotSize"][1])

            type1 = mt5.ORDER_TYPE_BUY if is_first_pair_long else mt5.ORDER_TYPE_SELL
            type2 = mt5.ORDER_TYPE_SELL if is_first_pair_long else mt5.ORDER_TYPE_BUY

            result1 = place_trade(pair1, lot1, type1, self.magic_number, comment)
            if not result1:
                print(f"Failed to place trade for {pair1}")
                return False

            result2 = place_trade(pair2, lot2, type2, self.magic_number, comment)
            if not result2:
                print(f"Failed to place trade for {pair2}, closing {pair1} trade")
                close_position(result1.order)
                return False

            print(f"Successfully placed paired trades: "
                  f"{'Long' if is_first_pair_long else 'Short'} {pair1}, "
                  f"{'Short' if is_first_pair_long else 'Long'} {pair2}")
            return True

        except Exception as e:
            print(f"Error placing trades: {e}")
            return False

    def _check_rsi_conditions(self, rsi1, rsi2):
        """
        Check if RSI conditions are met for trade entry.
        Returns True if conditions are met, False otherwise.
        """
        try:
            if rsi1 is None or rsi2 is None:
                return False

            overbought = float(self.params["rsiOverbought"])
            oversold = float(self.params["rsiOversold"])

            condition1 = rsi1 > overbought and rsi2 < oversold

            condition2 = rsi1 < oversold and rsi2 > overbought

            if condition1:
                print(f"RSI Conditions Met: {self.params['currencyPairs'][0]} overbought ({rsi1:.2f}), "
                      f"{self.params['currencyPairs'][1]} oversold ({rsi2:.2f})")
                return True
            elif condition2:
                print(f"RSI Conditions Met: {self.params['currencyPairs'][0]} oversold ({rsi1:.2f}), "
                      f"{self.params['currencyPairs'][1]} overbought ({rsi2:.2f})")
                return True
            else:
                print(f"RSI Conditions Not Met: {self.params['currencyPairs'][0]} RSI: {rsi1:.2f}, "
                      f"{self.params['currencyPairs'][1]} RSI: {rsi2:.2f}")
                return False

        except Exception as e:
            print(f"Error checking RSI conditions: {e}")
            return False

    async def stop(self, close_trades: bool = True):
        """Stop strategy and close all trades (optional)"""
        print(f"\nStopping strategy {self.strategy_id}")
        if close_trades:
            self.is_stopping = True
        closed_trades = 0
        failed_closures = 0

        active_trades = []
        open_trades = mt5.positions_get(magic=self.magic_number)
        for trade in open_trades:
            if trade.magic == self.magic_number:
                active_trades.append(trade)

        if not active_trades:
            print("No active trades found")
            return {
                "closed_trades": 0,
                "failed_closures": 0,
                "remaining_trades": 0
            }

        print(f"Found {len(active_trades)} trades to close")

        if close_trades:
            for trade in active_trades:
                try:
                    close_type = mt5.ORDER_TYPE_BUY if trade.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL
                    
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": trade.symbol,
                        "volume": trade.volume,
                        "type": close_type,
                        "position": trade.ticket,
                        "magic": self.magic_number,
                        "comment": "Strategy Stop Closure",
                        "type_time": mt5.ORDER_TIME_GTC
                    }

                    success = False
                    for filling_type in [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]:
                        close_request["type_filling"] = filling_type
                        result = mt5.order_send(close_request)
                        
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            closed_trades += 1
                            print(f"Successfully closed trade {trade.ticket} using filling type {filling_type}")
                            success = True
                            break
                        else:
                            print(f"Failed to close trade {trade.ticket} with filling type {filling_type}: "
                                f"{result.comment if result else 'No result'}")

                    if not success:
                        failed_closures += 1
                        print(f"Failed to close trade {trade.ticket} after all attempts")

                    await asyncio.sleep(0.1)

                except Exception as e:
                    failed_closures += 1
                    print(f"Error closing trade {trade.ticket}: {e}")

        open_trades = mt5.positions_get(magic=self.magic_number)
        remaining_trades = []
        for trade in open_trades:
            if trade.magic == self.magic_number:
                remaining_trades.append(trade)
        remaining_count = len(remaining_trades) if remaining_trades else 0

        status_message = (
            f"Strategy {self.strategy_id} stop results:\n"
            f"Attempted to close: {len(active_trades)} trades\n"
            f"Successfully closed: {closed_trades}\n"
            f"Failed to close: {failed_closures}\n"
            f"Remaining trades: {remaining_count}"
        )
        print(status_message)

        return {
            "closed_trades": closed_trades,
            "failed_closures": failed_closures,
            "remaining_trades": remaining_count,
            "details": status_message
        }


    async def _print_status(self):
        """Print current monitoring status"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n=== Strategy {self.strategy_id} Status at {current_time} ===")

            if self.monitored_trades:
                print(f"\nMonitoring {len(self.monitored_trades)} active trades:")
                for trade in self.monitored_trades:
                    try:
                        position = mt5.positions_get(ticket=trade.ticket)
                        if position:
                            position = position[0]
                            print(
                                f"Ticket {trade.ticket}: {trade.symbol} "
                                f"{'Buy' if trade.type == mt5.ORDER_TYPE_BUY else 'Sell'} "
                                f"{trade.volume} lots, "
                                f"Open Price: {trade.price_open}, "
                                f"Current Profit: ${position.profit:.2f}"
                            )
                    except Exception as e:
                        print(f"Error getting position {trade.ticket} details: {e}")

            pair1, pair2 = self.params["currencyPairs"]
            correlation = calculate_correlation(
                pair1, 
                pair2, 
                int(self.params["correlationWindow"]),
                self.timeframe  # Pass the numeric timeframe
            )
            
            print(f"\nMarket Conditions:")
            correlation_str = f"{correlation:.3f}" if correlation is not None else "N/A"
            print(f"Correlation: {correlation_str}")
            print(f"Entry Threshold: {self.params['entryThreshold']}")
            print(f"Exit Threshold: {self.params['exitThreshold']}")

            if not self.monitored_trades:
                rsi1 = calculate_rsi(
                    pair1, 
                    int(self.params["rsiPeriod"]),
                    self.timeframe  # Pass the numeric timeframe
                )
                rsi2 = calculate_rsi(
                    pair2, 
                    int(self.params["rsiPeriod"]),
                    self.timeframe  # Pass the numeric timeframe
                )
                
                print(f"\nRSI Values:")
                rsi1_str = f"{rsi1:.2f}" if rsi1 is not None else "N/A"
                rsi2_str = f"{rsi2:.2f}" if rsi2 is not None else "N/A"
                print(f"{pair1} RSI: {rsi1_str}")
                print(f"{pair2} RSI: {rsi2_str}")
                print(f"Overbought Level: {self.params['rsiOverbought']}")
                print(f"Oversold Level: {self.params['rsiOversold']}")

            if self.last_trade_time:
                time_since_last = datetime.now() - self.last_trade_time
                cooldown_remaining = self.cooldown_period - time_since_last
                if cooldown_remaining.total_seconds() > 0:
                    hours_remaining = cooldown_remaining.total_seconds() / 3600
                    print(f"\nCooldown Period: {hours_remaining:.1f} hours remaining")

            print("=" * 50)

        except Exception as e:
            print(f"Error in status printing: {e}")

    async def _close_position(self, position):
        try:
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": position.ticket,
                "magic": self.magic_number,
                "comment": "Exit Strategy",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            return result.retcode == mt5.TRADE_RETCODE_DONE
        except Exception as e:
            logger.error(f"Error closing trade {position.ticket}: {e}")
            return False

@app.post("/mt5/plot-indicators")
async def plot_indicators(request: IndicatorRequest):
    try:
        # Set date range
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=30)
        
        print(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")

        # Convert timeframe to MT5 timeframe
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1,
            240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1
        }
        
        mt5_timeframe = timeframe_map.get(request.timeFrame)
        if not mt5_timeframe:
            raise HTTPException(status_code=400, detail="Invalid timeframe")

        if not mt5.initialize():
            raise HTTPException(status_code=500, detail="Failed to initialize MT5")

        # Fetch historical data with error handling
        def get_rates(symbol):
            print(f"Fetching data for {symbol} in {mt5_timeframe} minute timeframe for {start_date} to {end_date}")
            rates = mt5.copy_rates_range(symbol, mt5_timeframe, start_date, end_date)
            if rates is None or len(rates) == 0:
                raise HTTPException(status_code=400, 
                    detail=f"Failed to get data for {symbol}. Error: {mt5.last_error()[1]}")
            return rates

        # Get data for both pairs
        rates1 = get_rates(request.currencyPairs[0])
        rates2 = get_rates(request.currencyPairs[1])

        # Convert to structured arrays and ensure same timestamps
        times1 = rates1['time']
        times2 = rates2['time']
        
        # Find common timestamps
        common_times = np.intersect1d(times1, times2)
        
        # Filter data to include only common timestamps
        mask1 = np.isin(times1, common_times)
        mask2 = np.isin(times2, common_times)
        
        rates1 = rates1[mask1]
        rates2 = rates2[mask2]

        print(f"Aligned data points: {len(rates1)} for both pairs")

        # Calculate indicators
        def calculate_rsi(prices, period):
            deltas = np.diff(prices)
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum()/period
            down = -seed[seed < 0].sum()/period
            rs = up/down
            rsi = np.zeros_like(prices)
            rsi[:period] = 100. - 100./(1. + rs)

            for i in range(period, len(prices)):
                delta = deltas[i - 1]
                if delta > 0:
                    upval = delta
                    downval = 0.
                else:
                    upval = 0.
                    downval = -delta

                up = (up * (period - 1) + upval) / period
                down = (down * (period - 1) + downval) / period
                rs = up/down
                rsi[i] = 100. - 100./(1. + rs)

            return rsi

        def calculate_correlation(prices1, prices2, window):
            correlation = np.full_like(prices1, np.nan, dtype=float)
            for i in range(window, len(prices1)):
                if i >= window:
                    correlation[i] = np.corrcoef(prices1[i-window:i], prices2[i-window:i])[0,1]
            return correlation

        # Calculate indicators
        rsi1 = calculate_rsi(rates1['close'], request.rsiPeriod)
        rsi2 = calculate_rsi(rates2['close'], request.rsiPeriod)
        correlation = calculate_correlation(rates1['close'], rates2['close'], request.correlationWindow)

        # Create the plot
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), dpi=100)
        
        # Convert timestamps to datetime
        dates = [datetime.fromtimestamp(x) for x in rates1['time']]

        # Plot correlation
        ax1.plot(dates, correlation, 'w-', label='Correlation', alpha=0.8)
        ax1.axhline(y=request.entryThreshold, color='r', linestyle='--', label='Entry Threshold')
        ax1.axhline(y=request.exitThreshold, color='g', linestyle='--', label='Exit Threshold')
        ax1.set_title('Correlation Analysis')
        ax1.set_ylabel('Correlation')
        ax1.grid(True, alpha=0.2)
        ax1.legend()

        # Plot RSI
        ax2.plot(dates, rsi1, 'b-', label=f'RSI {request.currencyPairs[0]}', alpha=0.8)
        ax2.plot(dates, rsi2, 'y-', label=f'RSI {request.currencyPairs[1]}', alpha=0.8)
        ax2.axhline(y=request.rsiOverbought, color='r', linestyle='--', label='Overbought')
        ax2.axhline(y=request.rsiOversold, color='g', linestyle='--', label='Oversold')
        ax2.set_title('RSI Analysis')
        ax2.set_ylabel('RSI')
        ax2.grid(True, alpha=0.2)
        ax2.legend()

        # Format x-axis dates
        fig.autofmt_xdate()

        # Save plot to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return {
            "image": base64.b64encode(buf.getvalue()).decode('utf-8'),
            "statistics": {
                "dataPoints": len(rates1),
                "startDate": dates[0].strftime("%Y-%m-%d %H:%M"),
                "endDate": dates[-1].strftime("%Y-%m-%d %H:%M"),
                "pair1": request.currencyPairs[0],
                "pair2": request.currencyPairs[1]
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating indicator plot: {str(e)}")
    finally:
        mt5.shutdown()

@app.get("/mt5/available-data-range")
async def get_available_data_range(symbol: str, timeframe: int) -> Dict:
    try:
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return {"error": "Failed to initialize MT5", "status": "error"}

        # Check if symbol exists
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            available_symbols = mt5.symbols_get()
            symbol_names = [s.name for s in available_symbols]
            return {
                "error": f"Symbol {symbol} not found",
                "status": "error",
                "available_symbols": symbol_names[:10]  # First 10 symbols for reference
            }

        # Map timeframe
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1,
            240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1,
        }

        mt5_timeframe = timeframe_map.get(timeframe)
        if mt5_timeframe is None:
            return {
                "error": f"Invalid timeframe: {timeframe}",
                "status": "error",
                "valid_timeframes": list(timeframe_map.keys())
            }

        # Get the newest data
        newest_rates = mt5.copy_rates_from(
            symbol, 
            mt5_timeframe, 
            datetime.now(), 
            1
        )

        oldest_rates = mt5.copy_rates_from(
            symbol, 
            mt5_timeframe, 
            datetime(2000, 1, 1), 
            1000
        )

        if newest_rates is None:
            return {
                "error": "Could not fetch latest data",
                "status": "error",
                "symbol": symbol,
                "timeframe": timeframe
            }
            
        if oldest_rates is None:
            return {
                "error": "Could not fetch oldest data",
                "status": "error",
                "symbol": symbol,
                "timeframe": timeframe
            }

        # Calculate date range
        start_date = datetime.fromtimestamp(oldest_rates[0]['time'])
        end_date = datetime.fromtimestamp(newest_rates[0]['time'])
        
        # Return successful response
        return {
            "status": "success",
            "symbol": symbol,
            "timeframe": timeframe,
            "data_range": {
                "start": start_date.strftime("%Y-%m-%d %H:%M"),
                "end": end_date.strftime("%Y-%m-%d %H:%M")
            },
            "total_bars": len(oldest_rates),
            "symbol_info": {
                "visible": symbol_info.visible,
                "trade_mode": symbol_info.trade_mode,
                "selected": symbol_info.select
            }
        }

    except Exception as e:
        logger.exception("Error in get_available_data_range")
        return {
            "error": str(e),
            "status": "error",
            "type": "unexpected_error"
        }

# Optional: Add a helper endpoint to get all available timeframes
@app.get("/mt5/available-timeframes")
async def get_available_timeframes():
    """Get list of all available timeframes"""
    return {
        "timeframes": [
            {"minutes": 1, "description": "1 minute (M1)"},
            {"minutes": 5, "description": "5 minutes (M5)"},
            {"minutes": 15, "description": "15 minutes (M15)"},
            {"minutes": 30, "description": "30 minutes (M30)"},
            {"minutes": 60, "description": "1 hour (H1)"},
            {"minutes": 240, "description": "4 hours (H4)"},
            {"minutes": 1440, "description": "1 day (D1)"}
        ]
    }

class MT5ConnectionManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MT5ConnectionManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def ensure_connection(self) -> bool:
        try:
            if not self.initialized:
                if not mt5.initialize():
                    logger.error("Failed to initialize MT5")
                    return False
                self.initialized = True
                
            if not mt5.terminal_info().connected:
                mt5.shutdown()
                self.initialized = False
                return self.ensure_connection()
                
            return True
            
        except Exception as e:
            logger.error(f"Error in MT5 connection: {e}")
            return False

    def shutdown(self):
        try:
            if self.initialized:
                mt5.shutdown()
                self.initialized = False
        except Exception as e:
            logger.error(f"Error shutting down MT5: {e}")

# Create global connection manager instance
connection_manager = MT5ConnectionManager()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)