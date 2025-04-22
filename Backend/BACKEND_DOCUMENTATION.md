# Correlation TradeSim Backend Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Installation and Setup](#installation-and-setup)
4. [Key Components](#key-components)
5. [How It Works](#how-it-works)
6. [Code Examples](#code-examples)
7. [Making Changes](#making-changes)
8. [Troubleshooting](#troubleshooting)

## Introduction

The Correlation TradeSim backend is the engine that powers the trading simulation application. It connects to MetaTrader 5 (MT5), processes market data, calculates trading indicators, and executes trading strategies based on currency pair correlations.

## System Architecture

```
┌─────────────────────────────────────┐
│           MetaTrader 5              │
│  (Trading Platform with Market Data) │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│           MT5 API Layer             │
│  (mt5_api.py, mt5_bridge.py)        │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│         Indicator Engine            │
│  (indicator_utils.py)               │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Communication Layer           │
│  (indicator_websocket.py)           │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│           Frontend                  │
│  (React Application)                │
└─────────────────────────────────────┘
```

## Installation and Setup

### Prerequisites

1. Python 3.7 or higher
2. MetaTrader 5 terminal installed on your computer
3. MT5 account with login credentials

### Step-by-Step Setup

1. Install required Python packages:

```bash
cd "Backend/TradeSim Emulator"
pip install -r requirements.txt
```

2. Update the MT5 connection parameters in `mt5_bridge.py`:

```python
# MT5 Connection Parameters
LOGIN = your_login_number  # Replace with your MT5 account number
PASSWORD = "your_password"  # Replace with your MT5 password
SERVER = "your_server"  # Replace with your MT5 server name
TERMINAL_PATH = r"path_to_your_mt5_terminal"  # Replace with path to your MT5 terminal
```

3. Start the backend server:

```bash
python serve_indicators.py
```

This will start the WebSocket server for real-time indicators and the HTTP API server for strategy management.

## Key Components

### 1. MT5 API (`mt5_api.py`)

This is the main file that handles interaction with MetaTrader 5. It includes:

- **Connection Management**: Connects to MT5 and maintains the connection
- **Data Retrieval**: Gets historical price data and current market information
- **Trading Functions**: Opens and closes positions, manages orders
- **Backtesting Engine**: Simulates trading strategies on historical data

The most important class is `PairedTradingBacktester`, which implements the correlation-based trading strategy.

### 2. Indicator WebSocket (`indicator_websocket.py`)

This component provides real-time indicator data through WebSockets:

- **WebSocket Server**: Manages client connections
- **Real-time Calculations**: Continuously calculates and streams indicator values
- **Connection Management**: Handles multiple client connections and disconnections

### 3. Indicator Utilities (`indicator_utils.py`)

Contains helper functions for calculating technical indicators:

- **RSI Calculation**: Computes the Relative Strength Index
- **Correlation Calculation**: Measures the relationship between two currency pairs
- **Tick Data Retrieval**: Gets the latest price ticks from MT5

### 4. MT5 Bridge (`mt5_bridge.py`)

Provides tools for analyzing currency correlations:

- **Historical Data Analysis**: Analyzes past correlations between currency pairs
- **Visualization**: Generates plots and charts of correlation data
- **Statistical Analysis**: Calculates metrics about correlation patterns

## How It Works

### Connection Flow

1. The backend initializes a connection to MetaTrader 5 using your account credentials.
2. Once connected, it can access market data and execute trades.
3. The WebSocket server starts and waits for connections from the frontend.
4. When a client connects, it begins streaming real-time indicator data.

### Backtesting Process

1. User defines a strategy with parameters (currency pairs, timeframe, thresholds, etc.)
2. The backend fetches historical data for the specified period
3. It calculates indicators (RSI, correlation) for each time point
4. It simulates trades based on the strategy rules
5. It calculates performance metrics (profit/loss, win rate, etc.)
6. Results are returned to the frontend for display

### Live Trading Process

1. User starts a strategy from the frontend
2. The backend begins monitoring real-time market data
3. It calculates indicators and checks for entry/exit conditions
4. When conditions are met, it executes trades through MT5
5. Trade status and results are sent back to the frontend

## Code Examples

### Connecting to MT5

```python
def connect_mt5():
    """Initialize and connect to MT5 terminal"""
    if not mt5.initialize(
        path=TERMINAL_PATH,
        login=LOGIN,
        password=PASSWORD,
        server=SERVER
    ):
        print(f"MT5 initialization failed. Error code: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    print(f"MetaTrader5 package version: {mt5.__version__}")
    print(f"Connected to account #{mt5.account_info().login}")
    return True
```

### Calculating RSI

```python
def calculate_rsi(symbol: str, period: int, timeframe: int) -> float:
    """Calculate Relative Strength Index for a symbol"""
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
    
    # Get price data
    rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, period + 1)
    prices = pd.Series([rate['close'] for rate in rates])
    
    # Calculate RSI
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1])
```

### Calculating Correlation

```python
def calculate_correlation(pair1: str, pair2: str, window: int, timeframe: int) -> float:
    """Calculate correlation between two currency pairs"""
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
    
    # Get price data for both pairs
    rates1 = mt5.copy_rates_from_pos(pair1, mt5_timeframe, 0, window + 1)
    rates2 = mt5.copy_rates_from_pos(pair2, mt5_timeframe, 0, window + 1)
    
    prices1 = pd.Series([rate['close'] for rate in rates1])
    prices2 = pd.Series([rate['close'] for rate in rates2])
    
    # Calculate correlation
    correlation = prices1.rolling(window=window).corr(prices2).iloc[-1]
    
    return float(correlation)
```

### Trading Strategy Logic

```python
def check_entry_conditions(self, index):
    """Check if entry conditions are met at the given index"""
    # Get indicator values
    correlation = self.indicators['rolling_correlation'].iloc[index]
    pair1_rsi = self.indicators[f'{self.pair1}_rsi'].iloc[index]
    pair2_rsi = self.indicators[f'{self.pair2}_rsi'].iloc[index]
    
    # Check correlation threshold
    if correlation < self.correlation_entry_threshold:
        # Check RSI conditions for divergence
        if ((pair1_rsi > self.rsi_overbought and pair2_rsi < self.rsi_oversold) or
            (pair1_rsi < self.rsi_oversold and pair2_rsi > self.rsi_overbought)):
            return True
    
    return False
```

## Making Changes

### Adding a New Indicator

1. Open `indicator_utils.py`
2. Add a new function for your indicator:

```python
def calculate_my_indicator(symbol, parameters):
    # Get price data
    rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, lookback_period)
    prices = pd.Series([rate['close'] for rate in rates])
    
    # Calculate your indicator
    result = your_calculation_logic(prices, parameters)
    
    return result
```

3. Update `indicator_websocket.py` to include your new indicator in the data stream:

```python
async def calculate_indicators(self, strategy_id, params):
    # ... existing code ...
    
    # Add your new indicator
    my_indicator = calculate_my_indicator(symbol, parameters)
    
    # Include it in the message
    message = {
        "timestamp": current_time,
        "correlation": correlation,
        "rsi1": rsi1,
        "rsi2": rsi2,
        "my_indicator": my_indicator  # Add your indicator here
    }
    
    await self.broadcast(message, strategy_id)
```

### Modifying the Trading Strategy

1. Open `mt5_api.py`
2. Find the `PairedTradingBacktester` class
3. Modify the entry and exit conditions in the `run_backtest` method:

```python
def run_backtest(self):
    # ... existing code ...
    
    # Modify entry conditions
    if correlation < self.correlation_entry_threshold and your_new_condition:
        # Open a trade
        self._open_trade(index)
    
    # Modify exit conditions
    if correlation > self.correlation_exit_threshold or your_new_exit_condition:
        # Close the trade
        self._close_trade(index)
    
    # ... rest of the code ...
```

## Troubleshooting

### Common Issues

#### MT5 Connection Fails

**Problem**: Cannot connect to MetaTrader 5

**Solutions**:
- Make sure your MT5 terminal is running
- Check that your login credentials are correct
- Verify that the path to your MT5 terminal is correct
- Ensure your MT5 account has not been locked or disabled

#### Indicator Calculation Errors

**Problem**: Errors when calculating indicators

**Solutions**:
- Check that you have sufficient historical data for the selected timeframe
- Ensure the symbol names are correct and available in your MT5 terminal
- Verify that the timeframe is valid and supported

#### WebSocket Connection Issues

**Problem**: Frontend cannot connect to the WebSocket server

**Solutions**:
- Make sure the backend server is running
- Check that the WebSocket port is not blocked by a firewall
- Verify that the WebSocket URL in the frontend matches the backend server address

### Debugging Tips

1. Enable logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. Check MT5 error codes:

```python
if not mt5.initialize():
    print(f"MT5 initialization failed. Error code: {mt5.last_error()}")
```

3. Test indicator calculations with known data:

```python
# Test RSI calculation with sample data
test_prices = pd.Series([100, 102, 98, 101, 99, 103, 102, 105, 107, 106, 108, 109, 110, 112, 111])
test_delta = test_prices.diff()
test_gain = (test_delta.where(test_delta > 0, 0)).rolling(window=14).mean()
test_loss = (-test_delta.where(test_delta < 0, 0)).rolling(window=14).mean()
test_rs = test_gain / test_loss
test_rsi = 100 - (100 / (1 + test_rs))
print(f"Test RSI: {test_rsi.iloc[-1]}")
```

---

This documentation provides a detailed overview of the Correlation TradeSim backend. For more specific information, refer to the code comments and function documentation in the source files.