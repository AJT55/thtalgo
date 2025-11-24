"""
B-Xtrender Configuration File
==============================

This file contains all customizable parameters for the B-Xtrender indicator
and data fetching. Modify these values to adjust the indicator's behavior.

Author: Angel Huerta
Version: 2.0
Last Updated: November 23, 2025
"""

# ============================================================================
# B-XTRENDER INDICATOR PARAMETERS
# ============================================================================
# These parameters control the B-Xtrender calculation.
# Based on the original PineScript indicator by @Puppytherapy
#
# Sensitivity Guide:
#   - Lower values = More sensitive (more signals, more noise)
#   - Higher values = Less sensitive (fewer signals, smoother)
#
# Default values are optimized for daily/weekly/monthly timeframes
# ============================================================================

BX_TRENDER_PARAMS = {
    # Short-term Xtrender (Oscillator) Parameters
    # --------------------------------------------
    'short_l1': 5,   # First EMA period
                     # Lower = faster response to price changes
                     # Higher = smoother, less whipsaws
                     # Recommended range: 3-10
    
    'short_l2': 20,  # Second EMA period
                     # This creates the differential with short_l1
                     # Recommended range: 15-30
    
    'short_l3': 15,  # RSI period for short-term
                     # Standard RSI length, affects momentum calculation
                     # Recommended range: 10-20
    
    # Long-term Xtrender (Trend) Parameters
    # --------------------------------------
    'long_l1': 20,   # Long-term EMA period
                     # Defines the trend timeframe
                     # Recommended range: 15-30
    
    'long_l2': 15,   # Long-term RSI period
                     # Recommended range: 10-20
    
    't3_length': 5,  # T3 moving average length
                     # Used for smoothing the short-term Xtrender
                     # Recommended range: 3-7
}

# ============================================================================
# DATA FETCHING PARAMETERS
# ============================================================================
# Default parameters for data fetching via YFinance
# These are used by data_handler.py when no parameters are explicitly provided
# ============================================================================

DATA_PARAMS = {
    'symbol': 'AAPL',       # Trading symbol
                            # Examples: 'MSFT', 'GOOGL', 'TSLA', 'BTC-USD'
    
    'period': '2y',         # Historical data period
                            # Valid options: '1d', '5d', '1mo', '3mo', '6mo', 
                            #                '1y', '2y', '5y', '10y', 'ytd', 'max'
    
    'interval': '1d',       # Data interval/timeframe
                            # Valid options: '1m', '2m', '5m', '15m', '30m', '60m', '90m',
                            #                '1h', '1d', '5d', '1wk', '1mo', '3mo'
    
    'start_date': '2023-01-01',  # Optional: specific start date (YYYY-MM-DD)
    'end_date': None,            # Optional: specific end date (None = today)
}

# ============================================================================
# STRATEGY PARAMETERS (Backtrader)
# ============================================================================
# Parameters for backtesting with Backtrader framework
# ============================================================================

STRATEGY_PARAMS = {
    'initial_capital': 100000,  # Starting capital in USD
    'commission': 0.001,        # Commission per trade (0.1%)
    'position_size': 0.1,       # Position size as fraction of capital (10%)
}

# ============================================================================
# BACKTESTING PARAMETERS
# ============================================================================
# Control backtest output and visualization
# ============================================================================

BACKTEST_PARAMS = {
    'plot_results': True,   # Show backtest charts
    'print_results': True,  # Print performance statistics
}

# ============================================================================
# VISUALIZATION PARAMETERS
# ============================================================================
# Parameters for the multi-timeframe visualization (bxtrender_panel.py)
# ============================================================================

VISUALIZATION_PARAMS = {
    # Historical data periods for each timeframe
    'weekly_period': '5y',    # Weekly data: 5 years recommended (260 bars)
    'monthly_period': '10y',  # Monthly data: 10 years recommended (120 bars)
    
    # Chart appearance
    'histogram_range': [-50, 50],  # Y-axis range for B-Xtrender histograms
    'show_entry_signals': True,     # Show/hide entry signal markers
    'save_html': True,              # Auto-save HTML output
    
    # Signal generation
    'require_monthly_confirmation': True,  # Wait for monthly close before weekly entries
    'conservative_mode': True,             # Next-month entry (True) vs same-month (False)
}

# ============================================================================
# RISK MANAGEMENT PARAMETERS (Future Enhancement)
# ============================================================================
# Placeholder for future risk management features
# ============================================================================

RISK_PARAMS = {
    'position_size_pct': 2.0,      # % of capital per trade
    'max_positions': 5,             # Maximum concurrent positions
    'stop_loss_pct': 5.0,          # Stop loss percentage
    'take_profit_pct': 15.0,       # Take profit percentage
}

# ============================================================================
# NOTES FOR CUSTOMIZATION
# ============================================================================
# 
# For Different Asset Classes:
# -----------------------------
# Stocks/ETFs:     Use default parameters
# Crypto:          Consider shorter periods (short_l1=3, short_l2=15)
# Forex:           May need longer smoothing (short_l1=7, short_l2=25)
# Commodities:     Test with various parameters
#
# For Different Timeframes:
# -------------------------
# Intraday (1h):   Reduce all periods by 50%
# Daily:           Use default parameters
# Weekly:          Increase all periods by 50%
# Monthly:         Use caution - limited data points
#
# To Apply Changes:
# -----------------
# 1. Edit this file with your preferred parameters
# 2. Save the file
# 3. Run: python bxtrender_panel.py
# 4. New settings will be applied automatically
#
# ============================================================================
