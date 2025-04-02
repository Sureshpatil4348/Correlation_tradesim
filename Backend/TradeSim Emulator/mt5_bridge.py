import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

# MT5 Connection Parameters
LOGIN = 79689615
PASSWORD = "SVsv12!@4348"
SERVER = "Exness-MT5Trial8"
TERMINAL_PATH = r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"

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

def get_historical_data(symbol, timeframe=mt5.TIMEFRAME_H1, start_date=None):
    """Get historical price data for a symbol"""
    timezone = pytz.timezone("UTC")
    if start_date is None:
        start_date = datetime(2020, 1, 1, tzinfo=timezone)
    
    # Use a large number to ensure we get data from 2020
    rates = mt5.copy_rates_from(symbol, timeframe, datetime.now(timezone), 50000)
    if rates is None:
        print(f"Error getting historical data for {symbol}: {mt5.last_error()}")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    df = df[df['time'] >= pd.Timestamp(start_date)]
    return df

def analyze_correlation_pairs(pair1, pair2, period=20, start_date=datetime(2020, 1, 1, tzinfo=pytz.timezone("UTC"))):
    """Analyze correlation between two currency pairs"""
    # Get data for both pairs
    df1 = get_historical_data(pair1, start_date=start_date)
    df2 = get_historical_data(pair2, start_date=start_date)
    
    if df1 is None or df2 is None:
        print(f"Failed to retrieve data for {pair1} or {pair2}")
        return None, None, None, None
    
    # Align the dataframes on the time index
    df1.set_index('time', inplace=True)
    df2.set_index('time', inplace=True)
    
    # Make sure we have data for both pairs at the same times
    common_index = df1.index.intersection(df2.index)
    df1 = df1.loc[common_index]
    df2 = df2.loc[common_index]
    
    # Calculate returns
    df1['returns'] = df1['close'].pct_change()
    df2['returns'] = df2['close'].pct_change()
    
    # Calculate rolling correlation
    correlation = df1['returns'].rolling(period).corr(df2['returns'])
    
    # Count occurrences below thresholds
    below_025 = len(correlation[correlation < 0.25])
    below_0 = len(correlation[correlation < 0.0])
    below_neg025 = len(correlation[correlation < -0.25])
    
    stats = {
        'avg_corr': correlation.mean(),
        'below_025': below_025,
        'below_0': below_0,
        'below_neg025': below_neg025,
        'total_periods': len(correlation.dropna()),
        'pct_below_025': below_025 / len(correlation.dropna()) * 100 if len(correlation.dropna()) > 0 else 0,
        'pct_below_0': below_0 / len(correlation.dropna()) * 100 if len(correlation.dropna()) > 0 else 0,
        'pct_below_neg025': below_neg025 / len(correlation.dropna()) * 100 if len(correlation.dropna()) > 0 else 0,
        'min_date': correlation.index.min().strftime('%Y-%m-%d'),
        'max_date': correlation.index.max().strftime('%Y-%m-%d')
    }
    
    # Reset index for plotting
    correlation = correlation.reset_index()
    
    return correlation, df1.reset_index(), df2.reset_index(), stats

def format_stats_text(pair1, pair2, stats):
    """Format correlation statistics as HTML for display in the plot"""
    return (
        f"<b>{pair1} vs {pair2} Correlation</b><br>"
        f"Average: {stats['avg_corr']:.3f}<br>"
        f"Below 0.25: {stats['below_025']} ({stats['pct_below_025']:.1f}%)<br>"
        f"Below 0.00: {stats['below_0']} ({stats['pct_below_0']:.1f}%)<br>"
        f"Below -0.25: {stats['below_neg025']} ({stats['pct_below_neg025']:.1f}%)<br>"
        f"Total periods: {stats['total_periods']}"
    )

def plot_correlation_analysis():
    """Plot correlation for multiple currency pair combinations"""
    # Currency pair combinations to analyze
    pair_combinations = [
        ('GBPUSD', 'EURUSD', 'GBP/USD vs EUR/USD Correlation'),
        ('EURAUD', 'EURNZD', 'EUR/AUD vs EUR/NZD Correlation'),
        ('AUDJPY', 'NZDJPY', 'AUD/JPY vs NZD/JPY Correlation')
    ]
    
    # Create a figure with three subplots with more vertical space
    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=[title for _, _, title in pair_combinations],
        vertical_spacing=0.2,  # Increased for more space
        row_heights=[0.33, 0.33, 0.33]
    )
    
    # Process each pair combination
    colors = ['rgb(0,100,180)', 'rgb(0,120,160)', 'rgb(0,140,140)']
    min_date = datetime(2025, 1, 1)  # Initialize with a future date
    max_date = datetime(2020, 1, 1)  # Initialize with a past date
    
    for i, (pair1, pair2, title) in enumerate(pair_combinations):
        print(f"\nAnalyzing {pair1} vs {pair2} correlation:")
        
        # Analyze correlation
        correlation_data, df1, df2, stats = analyze_correlation_pairs(pair1, pair2)
        
        if correlation_data is not None:
            # Add correlation plot
            fig.add_trace(
                go.Scatter(
                    x=correlation_data['time'],
                    y=correlation_data['returns'],
                    name=f"{pair1} vs {pair2}",
                    line=dict(color=colors[i], width=1.5)
                ),
                row=i+1, col=1
            )
            
            # Track min and max dates across all datasets
            if pd.Timestamp(stats['min_date']) < min_date:
                min_date = pd.Timestamp(stats['min_date'])
            if pd.Timestamp(stats['max_date']) > max_date:
                max_date = pd.Timestamp(stats['max_date'])
            
            # Print statistics
            print(f"Average Correlation: {stats['avg_corr']:.3f}")
            print(f"Periods below 0.25: {stats['below_025']} ({stats['pct_below_025']:.1f}%)")
            print(f"Periods below 0.00: {stats['below_0']} ({stats['pct_below_0']:.1f}%)")
            print(f"Periods below -0.25: {stats['below_neg025']} ({stats['pct_below_neg025']:.1f}%)")
            print(f"Total analyzed periods: {stats['total_periods']}")
            print(f"Date range: {stats['min_date']} to {stats['max_date']}")
            
            # Add correlation threshold lines
            threshold_colors = ['rgba(255,0,0,0.3)', 'rgba(0,0,0,0.3)', 'rgba(0,255,0,0.3)']
            values = [0.25, 0.0, -0.25]
            labels = ['0.25', '0.00', '-0.25']
            for color, value, label in zip(threshold_colors, values, labels):
                fig.add_hline(
                    y=value,
                    line_dash="dash",
                    line_color=color,
                    line_width=1,
                    row=i+1, col=1,
                    annotation_text=label,
                    annotation_position="right"
                )
            
            # Add statistics as annotations to the plot
            stats_text = format_stats_text(pair1, pair2, stats)
            fig.add_annotation(
                xref=f"x{i+1}",
                yref=f"y{i+1}",
                x=0.02,  # Position at 2% from left
                y=0.95,  # Position at 95% from bottom
                text=stats_text,
                showarrow=False,
                align="left",
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="rgba(0, 0, 0, 0.3)",
                borderwidth=1,
                borderpad=6,
                font=dict(size=10),
                xanchor="left",
                yanchor="top"
            )
    
    # Update layout with more height for better spacing
    fig.update_layout(
        height=1500,  # Increased for better spacing
        title=dict(
            text="20-Period Rolling Correlations (2020-2025)",
            x=0.5,
            y=0.98,  # Moved higher to avoid overlap
            xanchor='center',
            yanchor='top',
            font=dict(size=20)
        ),
        showlegend=False,  # Disable legend to avoid overlapping
        margin=dict(t=100, b=50, l=50, r=50),  # Add margins
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Set the same x-axis range for all subplots
    buffer_days = pd.Timedelta(days=10)  # Add a small buffer on both sides
    date_min = min_date - buffer_days
    date_max = max_date + buffer_days
    
    # Update x-axes with better date formatting and fixed range
    for i in range(1, 4):
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=False,
            title_text="Date",
            tickformat="%b %Y",  # Month Year format
            range=[date_min, date_max],  # Fixed date range
            row=i, col=1
        )
    
    # Update y-axes
    for i in range(1, 4):
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(128,128,128,0.2)',
            zeroline=False,
            range=[-1, 1],
            title_text="Correlation",
            row=i, col=1,
            tickformat=".2f"  # Format with 2 decimal places
        )
    
    fig.show()

if __name__ == "__main__":
    if connect_mt5():
        plot_correlation_analysis()
        mt5.shutdown()
