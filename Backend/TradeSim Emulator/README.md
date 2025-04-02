# Currency Analysis Tools

This repository contains tools for analyzing currency correlations and strengths using the MetaTrader 5 API.

## Features

### 1. Currency Pair Correlation Analysis (`mt5_bridge.py`)
- Analyzes rolling correlations between different forex currency pairs
- Supports various timeframes
- Visualizes correlations with interactive Plotly charts
- Includes statistical analysis with thresholds

### 2. Currency Strength Meter (`currency_strength_meter.py`)
- Measures the relative strength of major currencies (USD, EUR, GBP, JPY, AUD, NZD, CAD, CHF)
- Interactive web dashboard using Dash
- Supports multiple timeframes (1m, 5m, 15m, 30m, 1h, 4h, 1d)
- Option for closed candle data or live updates
- Visual representation with color-coded strength bars

## Requirements
- Python 3.x
- MetaTrader 5 terminal installed
- Required Python packages (see requirements.txt)

## Installation
1. Install required packages:
```
pip install -r requirements.txt
```

2. Make sure your MetaTrader 5 terminal is running

## Usage

### Currency Pair Correlation Analysis
```
python mt5_bridge.py
```

### Currency Strength Meter
```
python currency_strength_meter.py
```
- The dashboard will open in your web browser at http://127.0.0.1:8050/
- Select the desired timeframe from the dropdown
- Choose between "Closed Candles Only" or "Live Updates"
- Click "Refresh" to manually update the data, or select "Live Updates" for automatic refreshing

## Parameters
- You can modify the MT5 connection parameters in each script:
  - LOGIN: Your MT5 account number
  - PASSWORD: Your MT5 password
  - SERVER: Your MT5 server name
  - TERMINAL_PATH: Path to your MT5 terminal executable

## Note
- The strength values are relative and normalized to a 0-100 scale for comparison
- The tools require an active MetaTrader 5 connection
