# Correlation TradeSim Frontend Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Installation and Setup](#installation-and-setup)
4. [Key Components](#key-components)
5. [Pages](#pages)
6. [State Management](#state-management)
7. [How It Works](#how-it-works)
8. [Making Changes](#making-changes)
9. [Troubleshooting](#troubleshooting)

## Introduction

The Correlation TradeSim frontend is a React-based web application that provides a user-friendly interface for traders to create, test, and run trading strategies based on currency pair correlations. It communicates with the backend to display real-time market data, manage trading strategies, and visualize backtest results.

## System Architecture

```
┌─────────────────────────────────────┐
│           React App                 │
│  (Main Application Container)        │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│         Component Layer             │
│  (Pages, UI Components)             │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│         State Management            │
│  (Zustand Store)                    │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│       Communication Layer           │
│  (HTTP APIs, WebSockets)            │
└───────────────┬─────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│           Backend                   │
│  (Python/MT5 Application)           │
└─────────────────────────────────────┘
```

## Installation and Setup

### Prerequisites

1. Node.js (version 14 or higher)
2. npm (comes with Node.js)
3. Backend server running (see Backend Documentation)

### Step-by-Step Setup

1. Navigate to the frontend directory:

```bash
cd "FrontEnd/TradeSim/tradesim"
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

## Key Components

### 1. App (`App.jsx`)

This is the main application component that:
- Manages authentication state
- Renders the navbar and sidebar
- Displays different pages based on navigation
- Shows loading indicators when needed

```jsx
const App = () => {
  const { isLoggedIn, setIsLoggedIn, isLoading } = useStore((state) => state);
  const { selectedPage } = useStore((state) => state);

  // Check login status on load
  useEffect(() => {
    // ... login check code ...
  }, []);

  return (
    <div>
      <Navbar />
      {!isLoggedIn ? (
        <LoginForm />  // Show login form if not logged in
      ) : (
        <>
          <Sidebar />
          {selectedPage === 'Dashboard' && <Dashboard />}
          {selectedPage === 'Strategies' && <Strategies />}
          {/* ... other pages ... */}
        </>
      )}
      {isLoading && <Loader />}
    </div>
  );
};
```

### 2. Navbar (`navbar.jsx`)

Displays the application header with:
- Application title/logo
- User account information
- Logout button

### 3. Sidebar (`sidebar.jsx`)

Provides navigation to different sections of the application:
- Dashboard
- Strategies
- Indicators
- Analytics
- Settings

### 4. Indicator Dashboard (`indicatorDashboard.jsx`)

Displays real-time indicators using WebSocket connections:
- Correlation between currency pairs
- RSI values
- Charts for visualizing indicator changes over time

```jsx
const IndicatorDashboard = ({ strategyId, parameters }) => {
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [indicatorData, setIndicatorData] = useState([]);
  const wsRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:5001/ws/${strategyId}`);
      wsRef.current = ws;

      ws.onopen = () => setWsStatus('connected');
      ws.onclose = () => setWsStatus('disconnected');
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setIndicatorData(prev => [...prev, data]);
      };
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [strategyId]);

  // Render charts and indicators
  return (
    <div>
      <div className="status-badge">{wsStatus}</div>
      <div className="metrics-grid">
        {/* Display current indicator values */}
      </div>
      <div className="chart-section">
        {/* Render correlation and RSI charts */}
      </div>
    </div>
  );
};
```

### 5. Login Form (`loginForm.jsx`)

Handles user authentication with MT5:
- Username/password input
- Server selection
- Login button
- Error handling

## Pages

### 1. Dashboard (`dashboard.jsx`)

Shows an overview of trading activity:
- Active trades
- Win rate
- Total profit
- Account balance and equity
- List of recent trades

```jsx
const Dashboard = () => {
  const { accountInfo, setAccountInfo } = useStore((state) => state);
  const [trades, setTrades] = useState([]);
  const [history, setHistory] = useState([]);
  const [totalProfit, setTotalProfit] = useState(0);

  useEffect(() => {
    // Fetch account info, trade history, and active trades
    const fetchData = async () => {
      // ... fetch data from backend ...
    };
    
    fetchData();
    const interval = setInterval(fetchTrades, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="status-badge">Connected to MT5 ({accountInfo.account_number})</div>
      
      <div className="metrics-grid">
        {/* Display active trades, win rate, profit */}
      </div>
      
      <div className="trade-history">
        {/* Display trade history table */}
      </div>
    </div>
  );
};
```

### 2. Strategies (`strategies.jsx`)

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

```jsx
const Strategies = () => {
  const { strategies, setStrategies } = useStore((state) => state);
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    currencyPairs: ['', ''],
    lotSize: [0, 0],
    timeFrame: '',
    // ... other parameters ...
  });

  const saveStrategyParameters = (e) => {
    e.preventDefault();
    // Save strategy logic
    // ...
  };

  const runBacktest = async (strategy) => {
    // Run backtest logic
    // ...
  };

  return (
    <div>
      <h2>Strategies</h2>
      
      {/* Strategy list or form based on state */}
      {selectedStrategy ? (
        <form onSubmit={saveStrategyParameters}>
          {/* Strategy form fields */}
        </form>
      ) : (
        <div className="strategy-list">
          {/* List of strategies with action buttons */}
        </div>
      )}
    </div>
  );
};
```

### 3. Indicators (`indicators.jsx`)

Displays real-time market indicators:
- Correlation between selected currency pairs
- RSI values for each currency pair
- Visual charts of indicator changes

## State Management

The frontend uses Zustand for state management (`useStore.js`):

```javascript
const useStore = create(
    persist(
        (set) => ({
            // Authentication state
            isLoggedIn: false,
            accountInfo: null,
            
            // UI state
            isLoading: false,
            selectedPage: 'Dashboard',
            
            // Application data
            strategies: [],
            strategyToBackTest: null,
            
            // Actions
            setIsLoggedIn: (isLoggedIn) => set({ isLoggedIn }),
            setAccountInfo: (accountInfo) => set({ accountInfo }),
            setStrategies: (strategies) => set({ strategies }),
            setSelectedPage: (page) => set({ selectedPage: page }),
            // ... other actions ...
        }),
        {
            name: 'trade-sim-store',
            storage: createJSONStorage(() => localStorage),
        }
    )
);
```

Key state elements:
- `isLoggedIn`: Tracks user authentication status
- `accountInfo`: Stores MT5 account information
- `strategies`: List of user-created trading strategies
- `selectedPage`: Currently active page in the application
- `isLoading`: Shows loading state during async operations

## How It Works

### Authentication Flow

1. When the application loads, it checks if the user is already logged in by calling the backend API
2. If not logged in, it displays the login form
3. User enters MT5 credentials and submits the form
4. The backend verifies the credentials with MT5
5. If successful, the frontend updates the login state and shows the main application

### Strategy Management Flow

1. User navigates to the Strategies page
2. They can view existing strategies or create a new one
3. When creating/editing a strategy, they fill out the form with parameters
4. On save, the strategy is stored in the application state and persisted to localStorage
5. The strategy can then be backtested or run live

### Real-time Indicator Flow

1. User selects a strategy to view indicators for
2. The frontend establishes a WebSocket connection to the backend
3. The backend starts calculating indicators in real-time
4. Indicator data is streamed to the frontend through the WebSocket
5. The frontend updates charts and displays with the latest data

## Making Changes

### Adding a New Page

1. Create a new file in `src/components/pages/`:

```jsx
// src/components/pages/myNewPage.jsx
import React from 'react';
import useStore from '../../stores/useStore';

const MyNewPage = () => {
  // Component state and logic
  
  return (
    <div>
      <h2>My New Page</h2>
      {/* Page content */}
    </div>
  );
};

export default MyNewPage;
```

2. Update `App.jsx` to include your new page:

```jsx
import MyNewPage from './components/pages/myNewPage';

const App = () => {
  // ... existing code ...
  
  return (
    <div>
      <Navbar />
      {!isLoggedIn ? (
        <LoginForm />
      ) : (
        <>
          <Sidebar />
          {selectedPage === 'Dashboard' && <Dashboard />}
          {selectedPage === 'Strategies' && <Strategies />}
          {selectedPage === 'MyNewPage' && <MyNewPage />} {/* Add your new page */}
          {/* ... other pages ... */}
        </>
      )}
    </div>
  );
};
```

3. Add a link to your page in the sidebar (`sidebar.jsx`):

```jsx
<div className="sidebar-item" onClick={() => setSelectedPage('MyNewPage')}>
  My New Page
</div>
```

### Adding a New Component

1. Create a new file in `src/components/`:

```jsx
// src/components/myNewComponent.jsx
import React from 'react';

const MyNewComponent = ({ prop1, prop2 }) => {
  return (
    <div className="my-component">
      <h3>{prop1}</h3>
      <p>{prop2}</p>
    </div>
  );
};

export default MyNewComponent;
```

2. Import and use your component in a page:

```jsx
import MyNewComponent from '../myNewComponent';

const SomePage = () => {
  return (
    <div>
      <h2>Some Page</h2>
      <MyNewComponent prop1="Hello" prop2="World" />
    </div>
  );
};
```

### Adding New State

1. Update the Zustand store in `useStore.js`:

```javascript
const useStore = create(
    persist(
        (set) => ({
            // ... existing state ...
            
            // Add your new state
            myNewState: initialValue,
            
            // Add an action to update it
            setMyNewState: (value) => set({ myNewState: value }),
        }),
        // ... persist options ...
    )
);
```

2. Use the new state in a component:

```jsx
import useStore from '../stores/useStore';

const MyComponent = () => {
  const { myNewState, setMyNewState } = useStore((state) => state);
  
  return (
    <div>
      <p>Current value: {myNewState}</p>
      <button onClick={() => setMyNewState('new value')}>Update</button>
    </div>
  );
};
```

## Troubleshooting

### Common Issues

#### Application Doesn't Load

**Problem**: The application fails to load or shows a blank screen

**Solutions**:
- Check the browser console for JavaScript errors
- Make sure all dependencies are installed (`npm install`)
- Verify that the development server is running (`npm run dev`)
- Clear browser cache and reload

#### Backend Connection Fails

**Problem**: Cannot connect to the backend server

**Solutions**:
- Make sure the backend server is running
- Check that the API URLs in the frontend code match your backend server address
- Verify that there are no CORS issues (backend should allow requests from frontend origin)
- Check network tab in browser developer tools for specific error messages

#### WebSocket Connection Issues

**Problem**: Real-time indicators not updating

**Solutions**:
- Check that the WebSocket connection is established (look for 'connected' status)
- Verify that your MT5 terminal is running and connected
- Make sure the currency pairs you selected are available in your MT5 terminal
- Check browser console for WebSocket errors

### Debugging Tips

1. Use React Developer Tools browser extension to inspect component state and props

2. Add console logs to track data flow:

```jsx
useEffect(() => {
  console.log('Component mounted');
  console.log('Initial data:', data);
  
  // ... your code ...
  
  return () => console.log('Component unmounted');
}, []);
```

3. Monitor network requests in browser developer tools:
   - Check the Network tab to see API calls and responses
   - Filter by 'WS' to see WebSocket communication

4. Test API endpoints directly:

```javascript
// In browser console
fetch('http://localhost:5001/mt5/status')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

---

This documentation provides a detailed overview of the Correlation TradeSim frontend. For more specific information, refer to the code comments and component documentation in the source files.