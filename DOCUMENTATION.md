# Correlation TradeSim Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [Backend Documentation](#backend-documentation)
   - [Setup and Installation](#backend-setup-and-installation)
   - [Components](#backend-components)
   - [How It Works](#how-the-backend-works)
   - [Key Functions](#key-backend-functions)
4. [Frontend Documentation](#frontend-documentation)
   - [Setup and Installation](#frontend-setup-and-installation)
   - [Components](#frontend-components)
   - [Pages](#frontend-pages)
   - [State Management](#state-management)
5. [How to Use the Application](#how-to-use-the-application)
6. [Making Changes](#making-changes)
7. [Troubleshooting](#troubleshooting)

## Introduction

Correlation TradeSim is a trading simulation application that helps traders analyze and backtest trading strategies based on currency pair correlations. The application connects to MetaTrader 5 (MT5) to get real-time market data and allows users to create, test, and run trading strategies.

## System Overview

![System Overview](https://i.imgur.com/XYZ123.png)

*Note: Replace with actual system diagram if available*

The system consists of two main parts:

1. **Backend**: A Python application that connects to MetaTrader 5, processes market data, calculates indicators, and executes trading strategies.

2. **Frontend**: A React web application that provides a user interface for creating strategies, viewing real-time indicators, and analyzing backtest results.

The backend and frontend communicate through HTTP APIs and WebSockets for real-time data.

## Backend Documentation

### Backend Setup and Installation

1. Make sure you have MetaTrader 5 installed on your computer.

2. Install the required Python packages:

```bash
pip install -r Backend/TradeSim\ Emulator/requirements.txt
```

3. Update the MT5 connection parameters in `mt5_bridge.py` with your MetaTrader 5 account details:

```python
# MT5 Connection Parameters
LOGIN = your_login_number
PASSWORD = "your_password"
SERVER = "your_server"
TERMINAL_PATH = r"path_to_your_mt5_terminal"
```

### Backend Components

#### 1. MT5 API (`mt5_api.py`)

This is the core of the backend that handles:
- Connection to MetaTrader 5
- Getting market data
- Calculating indicators (RSI, correlation)
- Executing trades
- Backtesting strategies

The main class is `PairedTradingBacktester` which implements the correlation-based trading strategy.

#### 2. Indicator WebSocket (`indicator_websocket.py`)

This component:
- Provides real-time indicator data through WebSockets
- Calculates and streams correlation and RSI values
- Manages connections from multiple clients

#### 3. Indicator Utilities (`indicator_utils.py`)

Contains helper functions for calculating indicators:
- RSI (Relative Strength Index)
- Correlation between currency pairs
- Getting tick data from MT5

#### 4. MT5 Bridge (`mt5_bridge.py`)

Provides tools for analyzing currency correlations:
- Connects to MT5
- Gets historical data
- Analyzes correlations between currency pairs
- Generates visualization plots

### How the Backend Works

1. **Connection to MT5**: The backend connects to your MetaTrader 5 terminal to access market data and execute trades.

2. **Data Processing**: It fetches historical price data for currency pairs and calculates indicators like RSI and correlation.

3. **Strategy Execution**: Based on the indicators and user-defined parameters, it can execute trading strategies by opening and closing positions in MT5.

4. **Backtesting**: It can simulate trading strategies on historical data to evaluate their performance.

5. **Real-time Indicators**: It streams real-time indicator values to the frontend through WebSockets.

### Key Backend Functions

#### Correlation Calculation

```python
def calculate_correlation(pair1, pair2, window, timeframe):
    # Gets price data for both currency pairs
    # Calculates the correlation coefficient over the specified window
    # Returns the correlation value (-1 to +1)
```

This function calculates how closely two currency pairs move together. A value of +1 means they move exactly the same way, -1 means they move in opposite directions, and 0 means no relationship.

#### RSI Calculation

```python
def calculate_rsi(symbol, period, timeframe):
    # Gets price data for the symbol
    # Calculates the Relative Strength Index
    # Returns the RSI value (0-100)
```

RSI measures the speed and change of price movements. Values above 70 typically indicate overbought conditions, while values below 30 indicate oversold conditions.

#### Backtesting

The `PairedTradingBacktester` class simulates trading based on correlation and RSI values:

```python
def run_backtest(self):
    # Loops through historical data
    # Applies the trading strategy rules
    # Simulates opening and closing trades
    # Calculates performance metrics
```

## Frontend Documentation

### Frontend Setup and Installation

1. Navigate to the frontend directory:

```bash
cd FrontEnd/TradeSim/tradesim
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The application will be available at http://localhost:5173 (or another port if 5173 is in use).

### Frontend Components

#### 1. App (`App.jsx`)

The main application component that:
- Manages authentication state
- Renders the navbar and sidebar
- Displays different pages based on navigation

#### 2. Navbar (`navbar.jsx`)

Displays the application header with:
- Application title
- User account information
- Logout button

#### 3. Sidebar (`sidebar.jsx`)

Provides navigation to different sections of the application:
- Dashboard
- Strategies
- Indicators
- Analytics
- Settings

#### 4. Indicator Dashboard (`indicatorDashboard.jsx`)

Displays real-time indicators:
- Correlation between currency pairs
- RSI values
- Charts for visualizing indicator changes over time

### Frontend Pages

#### 1. Dashboard (`dashboard.jsx`)

Shows an overview of trading activity:
- Active trades
- Win rate
- Total profit
- Account balance and equity
- List of recent trades

#### 2. Strategies (`strategies.jsx`)

Allows users to manage trading strategies:
- Create new strategies
- Edit existing strategies
- Delete strategies
- Run backtest on strategies
- Start/stop live trading with strategies

Strategy parameters include:
- Currency pairs
- Lot sizes
- Timeframe
- RSI period and thresholds
- Correlation window and thresholds

#### 3. Indicators (`indicators.jsx`)

Displays real-time market indicators:
- Correlation between selected currency pairs
- RSI values for each currency pair
- Visual charts of indicator changes

### State Management

The frontend uses Zustand for state management (`useStore.js`):

```javascript
const useStore = create(
    persist(
        (set) => ({
            isLoggedIn: false,
            accountInfo: null,
            strategies: [],
            // ... other state variables and actions
        })
    )
);
```

Key state elements:
- `isLoggedIn`: Tracks user authentication status
- `accountInfo`: Stores MT5 account information
- `strategies`: List of user-created trading strategies
- `selectedPage`: Currently active page in the application

## How to Use the Application

### 1. Login

1. Start the backend server and make sure your MT5 terminal is running.
2. Open the frontend application in your browser.
3. Enter your MT5 account credentials to log in.

### 2. Create a Strategy

1. Navigate to the Strategies page.
2. Click "Create New Strategy".
3. Enter a name for your strategy.
4. Configure the strategy parameters:
   - Select two currency pairs
   - Set lot sizes for each pair
   - Choose a timeframe
   - Set RSI period and thresholds
   - Set correlation window and thresholds
5. Save the strategy.

### 3. Backtest a Strategy

1. On the Strategies page, find your strategy in the list.
2. Click "Backtest" next to the strategy.
3. Set the backtest parameters:
   - Start and end dates
   - Initial balance
4. Click "Run Backtest".
5. View the backtest results, including:
   - Total profit/loss
   - Win rate
   - Maximum drawdown
   - Charts showing trade entries and exits

### 4. Run a Live Strategy

1. On the Strategies page, find your strategy in the list.
2. Click "Start" to begin live trading with the strategy.
3. Monitor the active trades on the Dashboard.
4. Click "Stop" when you want to stop the strategy.

## Making Changes

### Modifying the Backend

#### Adding a New Indicator

1. Open `indicator_utils.py`.
2. Add a new function for your indicator:

```python
def calculate_my_indicator(symbol, parameters):
    # Your indicator calculation code
    return indicator_value
```

3. Update `indicator_websocket.py` to include your new indicator in the data stream.

#### Changing the Trading Strategy

1. Open `mt5_api.py`.
2. Find the `PairedTradingBacktester` class.
3. Modify the `run_backtest` method to implement your strategy logic.

### Modifying the Frontend

#### Adding a New Page

1. Create a new file in `src/components/pages/`.
2. Create your page component.
3. Update `App.jsx` to include your new page in the routing.
4. Add a link to your page in the sidebar.

#### Customizing the Dashboard

1. Open `src/components/pages/dashboard.jsx`.
2. Modify the JSX to change the layout or add new elements.
3. Add new state variables or data fetching as needed.

## Troubleshooting

### Backend Issues

#### MT5 Connection Fails

- Make sure your MT5 terminal is running.
- Check that your login credentials in `mt5_bridge.py` are correct.
- Verify that the path to your MT5 terminal is correct.

#### Indicator Calculation Errors

- Check that you have sufficient historical data for the selected timeframe.
- Ensure the symbol names are correct and available in your MT5 terminal.

### Frontend Issues

#### Application Doesn't Load

- Make sure the backend server is running.
- Check the browser console for JavaScript errors.
- Verify that the API URLs in the frontend code match your backend server address.

#### Real-time Indicators Not Updating

- Check that the WebSocket connection is established.
- Verify that your MT5 terminal is running and connected.
- Make sure the currency pairs you selected are available in your MT5 terminal.

---

This documentation provides a basic overview of the Correlation TradeSim application. For more detailed information, refer to the code comments and function documentation in the source files.