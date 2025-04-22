# Correlation TradeSim Brain Map

## System Overview

```
                                 ┌─────────────────────────┐
                                 │                         │
                                 │    MetaTrader 5         │
                                 │    Trading Platform      │
                                 │                         │
                                 └───────────┬─────────────┘
                                             │
                                             │ Market Data
                                             │ & Trading
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                             BACKEND SYSTEM                                  │
│                                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐  │
│  │                     │    │                     │    │                 │  │
│  │  MT5 API Layer      │◄──►│  Indicator Engine   │◄──►│  WebSocket      │  │
│  │  (mt5_api.py,       │    │  (indicator_utils.py)│    │  Server        │  │
│  │   mt5_bridge.py)    │    │                     │    │  (indicator_    │  │
│  │                     │    │                     │    │   websocket.py) │  │
│  └─────────┬───────────┘    └─────────┬───────────┘    └────────┬────────┘  │
│            │                          │                          │          │
│            │                          │                          │          │
│            ▼                          ▼                          ▼          │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐  │
│  │                     │    │                     │    │                 │  │
│  │  Backtesting Engine │    │  Correlation        │    │  Real-time      │  │
│  │  (PairedTrading     │    │  Calculator         │    │  Data Stream    │  │
│  │   Backtester)       │    │                     │    │                 │  │
│  │                     │    │                     │    │                 │  │
│  └─────────────────────┘    └─────────────────────┘    └─────────────────┘  │
│                                                                             │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    │ HTTP APIs & WebSockets
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                             FRONTEND SYSTEM                                 │
│                                                                             │
│  ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────┐  │
│  │                     │    │                     │    │                 │  │
│  │  Communication      │    │  State Management   │    │  React          │  │
│  │  Layer              │    │  (Zustand Store)    │    │  Components     │  │
│  │  (API Services)     │    │                     │    │                 │  │
│  │                     │    │                     │    │                 │  │
│  └─────────┬───────────┘    └─────────┬───────────┘    └────────┬────────┘  │
│            │                          │                          │          │
│            │                          │                          │          │
│            ▼                          ▼                          ▼          │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                                                                         ││
│  │                           UI PAGES                                      ││
│  │                                                                         ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    ││
│  │  │             │  │             │  │             │  │             │    ││
│  │  │ Dashboard   │  │ Strategy    │  │ Backtest    │  │ Settings    │    ││
│  │  │ Page        │  │ Builder     │  │ Results     │  │ Page        │    ││
│  │  │             │  │             │  │             │  │             │    ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    ││
│  │                                                                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Breakdown

### Backend Components

#### 1. MT5 API Layer
- **Files**: `mt5_api.py`, `mt5_bridge.py`
- **Responsibilities**:
  - Connect to MetaTrader 5
  - Retrieve market data
  - Execute trades
  - Manage MT5 connection parameters

#### 2. Indicator Engine
- **Files**: `indicator_utils.py`
- **Responsibilities**:
  - Calculate RSI (Relative Strength Index)
  - Calculate correlation between currency pairs
  - Process tick data from MT5
  - Generate technical indicators

#### 3. WebSocket Server
- **Files**: `indicator_websocket.py`
- **Responsibilities**:
  - Stream real-time indicator data
  - Manage client connections
  - Push updates to frontend

#### 4. Backtesting Engine
- **Class**: `PairedTradingBacktester`
- **Responsibilities**:
  - Simulate trading strategies on historical data
  - Calculate performance metrics
  - Generate backtest reports
  - Optimize strategy parameters

#### 5. Correlation Calculator
- **Responsibilities**:
  - Analyze relationships between currency pairs
  - Identify trading opportunities
  - Calculate correlation coefficients
  - Track correlation changes over time

### Frontend Components

#### 1. Communication Layer
- **Responsibilities**:
  - Make HTTP API calls to backend
  - Establish WebSocket connections
  - Handle request/response cycles
  - Manage error handling

#### 2. State Management
- **Technology**: Zustand Store
- **Responsibilities**:
  - Maintain application state
  - Store user preferences
  - Cache indicator data
  - Track strategy configurations

#### 3. React Components
- **Responsibilities**:
  - Render UI elements
  - Handle user interactions
  - Display charts and tables
  - Implement responsive design

#### 4. UI Pages

##### Dashboard Page
- **Features**:
  - Real-time correlation matrix
  - Active strategies overview
  - Performance metrics
  - Market overview

##### Strategy Builder
- **Features**:
  - Create and edit trading strategies
  - Set entry/exit conditions
  - Configure correlation parameters
  - Set risk management rules

##### Backtest Results
- **Features**:
  - View historical performance
  - Analyze trade statistics
  - Compare strategy variations
  - Visualize equity curves

##### Settings Page
- **Features**:
  - Configure MT5 connection
  - Set application preferences
  - Manage user profile
  - Configure notification settings

## Data Flow

1. **Market Data Flow**:
   - MetaTrader 5 → MT5 API Layer → Indicator Engine → WebSocket Server → Frontend

2. **Strategy Creation Flow**:
   - Frontend Strategy Builder → Communication Layer → Backend → MT5 API Layer

3. **Backtesting Flow**:
   - Frontend Request → Backend Backtesting Engine → Results → Frontend Display

4. **Trading Execution Flow**:
   - Strategy Signal → Backend → MT5 API Layer → MetaTrader 5 → Market

## Key Interactions

1. **Correlation Analysis**:
   - Backend calculates correlations between currency pairs
   - Results streamed to frontend via WebSockets
   - Frontend displays correlation matrix with visual indicators

2. **Strategy Execution**:
   - User creates strategy in frontend
   - Backend validates and stores strategy
   - Backend monitors market conditions
   - When conditions met, backend executes trades via MT5

3. **Backtesting Process**:
   - User configures backtest parameters
   - Backend runs simulation on historical data
   - Performance metrics calculated
   - Results sent to frontend for visualization

4. **Real-time Monitoring**:
   - Backend continuously streams indicator updates
   - Frontend updates charts and displays in real-time
   - Alerts triggered based on user-defined conditions

## Technology Stack

### Backend
- **Language**: Python
- **Trading Platform**: MetaTrader 5
- **Communication**: WebSockets, HTTP APIs
- **Data Processing**: NumPy, Pandas (implied)

### Frontend
- **Framework**: React
- **State Management**: Zustand
- **UI Components**: Custom React components
- **Data Visualization**: Charts (implementation details not specified)

## Integration Points

1. **MT5 Integration**:
   - Connection parameters in `mt5_bridge.py`
   - Trading functions in `mt5_api.py`

2. **Frontend-Backend Communication**:
   - WebSocket for real-time data
   - HTTP APIs for strategy management

3. **User Authentication**:
   - Login with MT5 credentials
   - Session management in frontend

## Extensibility

1. **Adding New Indicators**:
   - Extend `indicator_utils.py`
   - Update WebSocket server to stream new data
   - Add visualization in frontend

2. **New Strategy Types**:
   - Extend backtesting engine
   - Add new strategy templates in frontend
   - Implement new entry/exit conditions

3. **Additional Features**:
   - Risk management tools
   - Portfolio analysis
   - Multi-account management
   - Advanced reporting