"""
B-Xtrender Multi-Timeframe Trading Signal Generator
====================================================

This module creates interactive visualizations of the B-Xtrender indicator across
multiple timeframes (weekly and monthly) and generates entry signals based on
multi-timeframe alignment.

Key Features:
- Multi-timeframe B-Xtrender calculation (weekly + monthly)
- Color-coded histogram bars (light/dark green/red)
- Conservative entry signal generation
- Interactive Plotly charts with zoom, pan, and hover details

Signal Logic:
1. Wait for monthly bar to close with "light" colors (increasing momentum)
2. Scan for weekly closes with light colors in the NEXT month
3. Generate entry signals when both conditions are met

Date Alignment:
- YFinance indexes monthly bars by the first day of the NEXT month
- Example: 2025-08-01 index contains JULY 2025 data (Jul 1-31)
- This is standard across financial data providers
- NO DATE SHIFTING is applied - raw YFinance dates are used

Author: Angel Huerta
Version: 2.0 (Raw YFinance Alignment)
Last Updated: November 23, 2025
"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
from data.data_handler import get_sample_data, DataHandler
from indicators.bxtrender import calculate_bxtrender
from indicators.fair_value_bands import calculate_fair_value_bands, FAIR_VALUE_PARAMS
from config import BX_TRENDER_PARAMS, DATA_PARAMS


def create_bxtrender_multi_timeframe(symbol='AAPL', periods={'weekly': '5y', 'monthly': '10y'}, save_html=False):
    """
    Create B-Xtrender multi-timeframe visualization with entry signals.
    
    This function generates a 2x2 grid visualization showing:
    - Top row: Weekly and monthly price candlesticks with entry signal markers
    - Bottom row: Weekly and monthly B-Xtrender histograms (color-coded)
    
    Entry Signal Generation Logic:
    ------------------------------
    1. Identify monthly bars that close with "light" colors (improving momentum)
       - Light Green: BX > 0 and increasing
       - Light Red: BX < 0 but increasing (bottoming signal)
    
    2. For each favorable monthly close, look for weekly closes with light colors
       in the NEXT month (conservative approach - wait for monthly confirmation)
    
    3. Generate entry signals when both conditions are met
    
    YFinance Date Indexing:
    -----------------------
    - Monthly bars are indexed by the first day of the NEXT month
    - Example: Index 2025-08-01 = July 2025 data (Jul 1-31)
    - This is how YFinance structures monthly data (industry standard)
    - NO shifting or manipulation is done to the dates
    
    Args:
        symbol (str): Trading symbol (e.g., 'AAPL', 'MSFT')
        periods (dict): Historical data periods for each timeframe
            Example: {'weekly': '5y', 'monthly': '10y'}
        save_html (bool): If True, saves the chart as an HTML file with timestamp
        save_html: Whether to save as HTML file
    """

    print(f"Loading multi-timeframe data for {symbol}...")

    results = {}
    timeframes = {}

    # Fetch and calculate for each timeframe
    for timeframe, period in periods.items():
        print(f"Loading {timeframe} data ({period})...")

        # Get data handler instance
        data_handler = DataHandler()

        if timeframe == 'weekly':
            interval = '1wk'
        elif timeframe == 'monthly':
            interval = '1mo'
        else:
            interval = '1d'  # fallback

        # Fetch data
        data = data_handler.get_data(
            symbol,
            period=period,
            interval=interval
        )

        if data is None or data.empty:
            print(f"No {timeframe} data available")
            continue

        print(f"Loaded {len(data)} {timeframe} data points")
        print("Calculating B-Xtrender indicator...")

        # Calculate B-Xtrender
        result = calculate_bxtrender(data, **BX_TRENDER_PARAMS)
        
        # Calculate Fair Value Bands
        print("Calculating Fair Value Bands...")
        result = calculate_fair_value_bands(result, **FAIR_VALUE_PARAMS)
        
        results[timeframe] = result
        timeframes[timeframe] = len(data)

    if not results:
        print("No data available for any timeframe")
        return

    print("Creating multi-timeframe B-Xtrender visualization with price action...")

    # Create 4-panel figure (2x2 grid)
    fig = make_subplots(
        rows=2, cols=2,
        shared_xaxes=False,
        vertical_spacing=0.1,
        horizontal_spacing=0.1,
        subplot_titles=(
            f'{symbol} Weekly Price ({timeframes.get("weekly", 0)} bars)',
            f'{symbol} Monthly Price ({timeframes.get("monthly", 0)} bars)',
            f'B-Xtrender Weekly ({timeframes.get("weekly", 0)} bars)',
            f'B-Xtrender Monthly ({timeframes.get("monthly", 0)} bars)'
        ),
        row_heights=[0.5, 0.5],
        column_widths=[0.5, 0.5]
    )

    # Process each timeframe and identify entry signals
    timeframe_order = ['weekly', 'monthly']
    weekly_result = results.get('weekly')
    monthly_result = results.get('monthly')

    # ============================================================================
    # ENTRY SIGNAL GENERATION
    # ============================================================================
    # This section identifies entry signals based on multi-timeframe alignment
    # 
    # Step 1: Find monthly bars that close with "light" colors (improving momentum)
    # Step 2: For each favorable monthly close, look for weekly light closes in NEXT month
    # Step 3: Generate entry signals when both conditions are met
    # ============================================================================
    
    entry_signals = []

    if weekly_result is not None and monthly_result is not None:
        # ---------------------------------------------------------------------
        # STEP 1: Identify Favorable Monthly Closes
        # ---------------------------------------------------------------------
        # A "favorable" monthly close has INCREASING B-Xtrender (light color)
        # - Light Green: BX > 0 and BX > previous BX
        # - Light Red: BX <= 0 and BX > previous BX (bottoming/improving)
        # ---------------------------------------------------------------------
        
        favorable_monthly_closes = []

        for monthly_date in monthly_result.index:
            monthly_val = monthly_result.loc[monthly_date, 'short_term_xtrender']
            monthly_prev = monthly_result.shift(1).loc[monthly_date, 'short_term_xtrender'] if monthly_date != monthly_result.index[0] else monthly_val

            # Check if monthly closed with increasing light colors
            monthly_increasing_light = (
                (monthly_val > 0 and monthly_val > monthly_prev) or  # positive and increasing (light green)
                (monthly_val <= 0 and monthly_val > monthly_prev)    # negative but increasing (light red)
            )

            if monthly_increasing_light:
                # Store this favorable monthly close
                # NOTE: We use RAW yfinance dates (no shifting applied)
                # Example: monthly_date = 2025-08-01 (contains July data)
                
                favorable_monthly_closes.append({
                    'monthly_close_date': monthly_date,  # Raw YFinance index
                    'month_represented': monthly_date.strftime('%Y-%m'),  # Month label
                    'monthly_bx': monthly_val  # B-Xtrender value at this monthly close
                })

        # ---------------------------------------------------------------------
        # STEP 2: Find Weekly Signals in NEXT Month After Monthly Confirmation
        # ---------------------------------------------------------------------
        # CONSERVATIVE APPROACH: We wait for the monthly bar to CLOSE before
        # looking for entry signals. Weekly signals occur in the NEXT month
        # after a favorable monthly close.
        #
        # Example:
        #   Monthly 2025-08 closes Light Red → Favorable
        #   Look for weekly signals in 2025-09 period (next month index)
        # ---------------------------------------------------------------------

        for monthly_info in favorable_monthly_closes:
            # Get the index position of this favorable monthly close
            monthly_idx = monthly_result.index.get_loc(monthly_info['monthly_close_date'])
            
            # Check if there's a next month available
            if monthly_idx + 1 < len(monthly_result.index):
                next_monthly_date = monthly_result.index[monthly_idx + 1]

                # Define the weekly search period (NEXT month after confirmation)
                # Start: next_monthly_date (e.g., 2025-09-01 if monthly close was 2025-08-01)
                # End: The following monthly index OR +1 month if at the end
                if monthly_idx + 2 < len(monthly_result.index):
                    period_end = monthly_result.index[monthly_idx + 2]
                else:
                    period_end = next_monthly_date + pd.DateOffset(months=1)
                
                # Find weekly bars within this period
                weekly_in_next_period = weekly_result[
                    (weekly_result.index >= next_monthly_date) &
                    (weekly_result.index < period_end)
                ]

                # -------------------------------------------------------------
                # STEP 3: Check Each Weekly Bar for Light Colors
                # -------------------------------------------------------------
                # For each weekly bar in the next month period, check if it
                # closed with "light" colors (increasing B-Xtrender)
                # -------------------------------------------------------------
                
                for weekly_date in weekly_in_next_period.index:
                    weekly_val = weekly_result.loc[weekly_date, 'short_term_xtrender']
                    weekly_prev = weekly_result.shift(1).loc[weekly_date, 'short_term_xtrender'] if weekly_date != weekly_result.index[0] else weekly_val

                    # Check if weekly closed with increasing light colors
                    weekly_increasing_light = (
                        (weekly_val > 0 and weekly_val > weekly_prev) or  # Light Green
                        (weekly_val <= 0 and weekly_val > weekly_prev)    # Light Red
                    )

                    if weekly_increasing_light:
                        # ✅ ENTRY SIGNAL: Both monthly and weekly show improving momentum!
                        entry_signals.append({
                            'weekly_date': weekly_date,  # When to enter (weekly close date)
                            'monthly_close_date': monthly_info['monthly_close_date'],  # Confirming monthly bar
                            'weekly_bx': weekly_val,  # Weekly B-Xtrender value
                            'monthly_bx': monthly_info['monthly_bx'],  # Monthly B-Xtrender value
                            'price': weekly_result.loc[weekly_date, 'Close'],  # Entry price
                            'confirmed_by_month': monthly_info['month_represented']  # Which month confirmed
                        })

    print(f"Found {len(entry_signals)} entry signals in months following favorable monthly closes")

    # Process each timeframe
    for col, timeframe in enumerate(timeframe_order):
        if timeframe not in results:
            continue

        result = results[timeframe].copy()

        # Price chart (top row)
        fig.add_trace(
            go.Candlestick(
                x=result.index,
                open=result['Open'],
                high=result['High'],
                low=result['Low'],
                close=result['Close'],
                name=f'{timeframe.title()} Price',
                showlegend=False
            ),
            row=1, col=col+1
        )
        
        # Add Fair Value Bands to price chart
        # Fair Value Basis (center line)
        trend_colors = ['lime' if x == 1 else 'red' for x in result['trend_direction']]
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result['fair_value'],
                mode='lines',
                name='Fair Value',
                line=dict(color='blue', width=2),
                showlegend=False,
                opacity=0.7
            ),
            row=1, col=col+1
        )
        
        # Threshold bands (with fill)
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result['threshold_upper'],
                mode='lines',
                name='Threshold Upper',
                line=dict(color='rgba(0,128,128,0.3)', width=1),
                showlegend=False,
                fill=None
            ),
            row=1, col=col+1
        )
        
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result['threshold_lower'],
                mode='lines',
                name='Threshold Lower',
                line=dict(color='rgba(255,0,0,0.3)', width=1),
                showlegend=False,
                fill='tonexty',
                fillcolor='rgba(128,128,128,0.2)'
            ),
            row=1, col=col+1
        )
        
        # Deviation bands (1x) - yellow/tan color
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result['deviation_upper_1x'],
                mode='lines',
                name='Deviation 1x Upper',
                line=dict(color='rgb(196,177,101)', width=1),
                showlegend=False
            ),
            row=1, col=col+1
        )
        
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result['deviation_lower_1x'],
                mode='lines',
                name='Deviation 1x Lower',
                line=dict(color='rgb(196,177,101)', width=1),
                showlegend=False
            ),
            row=1, col=col+1
        )
        
        # Deviation bands (2x) - pink/salmon color
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result['deviation_upper_2x'],
                mode='lines',
                name='Deviation 2x Upper',
                line=dict(color='rgb(255,107,107)', width=1),
                showlegend=False
            ),
            row=1, col=col+1
        )
        
        fig.add_trace(
            go.Scatter(
                x=result.index,
                y=result['deviation_lower_2x'],
                mode='lines',
                name='Deviation 2x Lower',
                line=dict(color='rgb(255,107,107)', width=1),
                showlegend=False
            ),
            row=1, col=col+1
        )

        # Add entry signal markers on price charts
        if timeframe == 'weekly' and entry_signals:
            signal_dates = [s['weekly_date'] for s in entry_signals]
            signal_prices = [s['price'] for s in entry_signals]

            # Create detailed labels showing weekly entry and confirming monthly
            signal_labels = []
            for signal in entry_signals:
                weekly_str = signal['weekly_date'].strftime("%m/%d")
                confirmed_month = signal['confirmed_by_month']
                signal_labels.append(f'ENTRY<br>W:{weekly_str}<br>Confirmed by<br>{confirmed_month}')

            fig.add_trace(
                go.Scatter(
                    x=signal_dates,
                    y=signal_prices,
                    mode='markers+text',
                    marker=dict(
                        symbol='star',
                        size=14,
                        color='gold',
                        line=dict(width=2, color='orange')
                    ),
                    text=signal_labels,
                    textposition='top center',
                    textfont=dict(size=8, color='black', weight='bold'),
                    name='Entry Signals',
                    showlegend=False
                ),
                row=1, col=col+1
            )

        # B-Xtrender histogram (bottom row)
        # Create color-coded bars based on PineScript logic
        short_colors = []
        for idx in result.index:
            val = result.loc[idx, 'short_term_xtrender']
            prev_val = result.loc[idx, 'short_term_xtrender'] if idx == result.index[0] else result.shift(1).loc[idx, 'short_term_xtrender']

            if val > 0:
                if val > prev_val:
                    short_colors.append('lime')  # Positive and increasing
                else:
                    short_colors.append('#228B22')  # Positive but decreasing (darker green)
            else:
                if val > prev_val:
                    short_colors.append('red')  # Negative but increasing
                else:
                    short_colors.append('#8B0000')  # Negative and decreasing (darker red)

        fig.add_trace(
            go.Bar(
                x=result.index,
                y=result['short_term_xtrender'],
                name=f'{timeframe.title()} B-Xtrender',
                marker_color=short_colors,
                opacity=0.5,  # transp = 50 in PineScript
                showlegend=False
            ),
            row=2, col=col+1
        )

        # Add zero line to histogram
        fig.add_hline(y=0, line_dash='solid', line_color='black', opacity=1, row=2, col=col+1)

    # Update layout
    fig.update_layout(
        title=dict(
            text=f'B-Xtrender Multi-Timeframe Entry Signals (Close-Based) - {symbol}<br><sub>Gold stars show entry signals when both weekly & monthly closes show increasing light colors</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=14, color='black')
        ),
        height=800,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Update y-axes
    # Price charts
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=2)

    # Histogram charts
    fig.update_yaxes(title_text="B-Xtrender", range=[-50, 50], row=2, col=1)
    fig.update_yaxes(title_text="B-Xtrender", range=[-50, 50], row=2, col=2)

    # Format x-axes to avoid confusion
    # Weekly x-axis (bottom-left) - show dates
    fig.update_xaxes(
        tickformat="%Y-%m-%d",
        tickangle=45,
        row=2, col=1,
        title_text="Weekly Dates"
    )

    # Monthly x-axis (bottom-right) - show represented months
    fig.update_xaxes(
        tickformat="%b %Y",
        tickangle=45,
        row=2, col=2,
        title_text="Month Represented"
    )

    # Save as HTML if requested
    if save_html:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'bxtrender_multitimeframe_with_price_{symbol}_{timestamp}.html'
        fig.write_html(filename)
        print(f"Multi-timeframe chart with price action saved as {filename}")

    fig.show()

    # Print statistics for each timeframe
    for timeframe, result in results.items():
        print(f"\n{timeframe.title()} Statistics:")
        print(f"Price Range: ${result['Low'].min():.2f} - ${result['High'].max():.2f}")
        print(f"B-Xtrender Range: {result['short_term_xtrender'].min():.2f} to {result['short_term_xtrender'].max():.2f}")
        print(f"B-Xtrender Mean: {result['short_term_xtrender'].mean():.4f}")
        print(f"B-Xtrender Above zero: {(result['short_term_xtrender'] > 0).sum()} bars")
        print(f"B-Xtrender Below zero: {(result['short_term_xtrender'] < 0).sum()} bars")

    # Print entry signal details
    print(f"\n📊 Entry Signal Analysis:")
    print(f"Total Entry Signals: {len(entry_signals)}")
    if entry_signals:
        print("Entry signals occur in the NEXT month AFTER monthly closes with light colors:")
        print("- Monthly closes with light colors (establishes confirmation)")
        print("- Weekly closes with light colors in the FOLLOWING month")
        print("- More conservative: waits for monthly confirmation before entering")
        print("\nAll signals:")
        for signal in entry_signals:
            print(f"  Weekly {signal['weekly_date'].strftime('%Y-%m-%d')}: Price=${signal['price']:.2f}, Weekly BX={signal['weekly_bx']:.2f}")
            print(f"    └─ Confirmed by {signal['confirmed_by_month']} monthly close: BX={signal['monthly_bx']:.2f}")

    return fig, results, entry_signals


def get_bxtrender_histogram_data(symbol='AAPL', days=500):
    """
    Get just the B-Xtrender histogram data without visualization

    Args:
        symbol: Trading symbol
        days: Number of days of data

    Returns:
        pandas.Series: B-Xtrender histogram values with datetime index
    """
    data = get_sample_data(symbol, days)
    if data is None:
        return None

    result = calculate_bxtrender(data, **BX_TRENDER_PARAMS)
    return result['short_term_xtrender']


def get_bxtrender_multitimeframe_data(symbol='AAPL', periods={'weekly': '2y', 'monthly': '5y'}):
    """
    Get B-Xtrender data for multiple timeframes

    Args:
        symbol: Trading symbol
        periods: Dict with timeframe names and periods

    Returns:
        dict: Dictionary with timeframe names as keys and B-Xtrender series as values
    """
    results = {}

    for timeframe, period in periods.items():
        data_handler = DataHandler()

        if timeframe == 'weekly':
            interval = '1wk'
        elif timeframe == 'monthly':
            interval = '1mo'
        else:
            interval = '1d'

        data = data_handler.get_data(symbol, period=period, interval=interval)
        if data is not None:
            result = calculate_bxtrender(data, **BX_TRENDER_PARAMS)
            results[timeframe] = result['short_term_xtrender']

    return results


def create_bxtrender_panel(symbol='AAPL', days=500, save_html=False):
    """
    Create B-Xtrender panel visualization in PineScript style

    Args:
        symbol: Trading symbol
        days: Number of days of data
        save_html: Whether to save as HTML file
    """

    print(f"Loading {days} days of {symbol} data...")
    data = get_sample_data(symbol, days)
    if data is None:
        print("No data available")
        return

    print(f"Loaded {len(data)} data points")
    print("Calculating B-Xtrender indicator...")
    result = calculate_bxtrender(data, **BX_TRENDER_PARAMS)
    print("Creating B-Xtrender panel visualization...")

    # Create the multi-panel figure
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        subplot_titles=(
            'Price Chart',
            'B-Xtrender Osc. - Short-term',
            'B-Xtrender Shadow - Short-term',
            'B-Xtrender Trend - Long-term'
        ),
        row_heights=[0.4, 0.2, 0.2, 0.2]
    )

    # 1. Price Chart with signals
    fig.add_trace(
        go.Candlestick(
            x=result.index,
            open=result['Open'],
            high=result['High'],
            low=result['Low'],
            close=result['Close'],
            name='Price',
            showlegend=False
        ),
        row=1, col=1
    )

    # Buy/Sell signals as shapes on price chart
    buy_signals = result[result['short_buy_signal'] == 1]
    sell_signals = result[result['short_sell_signal'] == 1]

    fig.add_trace(
        go.Scatter(
            x=buy_signals.index,
            y=buy_signals['Low'] * 0.998,
            mode='markers',
            marker=dict(symbol='triangle-up', size=10, color='lime', line=dict(width=1, color='darkgreen')),
            name='Buy Signal',
            showlegend=False
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=sell_signals.index,
            y=sell_signals['High'] * 1.002,
            mode='markers',
            marker=dict(symbol='triangle-down', size=10, color='red', line=dict(width=1, color='darkred')),
            name='Sell Signal',
            showlegend=False
        ),
        row=1, col=1
    )

    # 2. Short-term Xtrender Histogram (like PineScript)
    # Create color-coded bars based on conditions
    short_colors = []
    for idx in result.index:
        val = result.loc[idx, 'short_term_xtrender']
        prev_val = result.loc[idx, 'short_term_xtrender'] if idx == result.index[0] else result.shift(1).loc[idx, 'short_term_xtrender']

        if val > 0:
            if val > prev_val:
                short_colors.append('lime')  # Positive and increasing
            else:
                short_colors.append('#228B22')  # Positive but decreasing (darker green)
        else:
            if val > prev_val:
                short_colors.append('red')  # Negative but increasing
            else:
                short_colors.append('#8B0000')  # Negative and decreasing (darker red)

    fig.add_trace(
        go.Bar(
            x=result.index,
            y=result['short_term_xtrender'],
            name='Short-term Xtrender',
            marker_color=short_colors,
            opacity=0.7,
            showlegend=False
        ),
        row=2, col=1
    )

    # 3. Short-term Xtrender Shadow (T3 smoothed version)
    # Black shadow line (thick)
    fig.add_trace(
        go.Scatter(
            x=result.index,
            y=result['ma_short_term_xtrender'],
            mode='lines',
            name='Shadow',
            line=dict(color='black', width=5),
            showlegend=False
        ),
        row=3, col=1
    )

    # Color line on top (thinner)
    ma_short_trend = result['ma_short_term_xtrender'] > result['ma_short_term_xtrender'].shift(1)
    ma_colors = ['lime' if x else 'red' for x in ma_short_trend]
    fig.add_trace(
        go.Scatter(
            x=result.index,
            y=result['ma_short_term_xtrender'],
            mode='lines',
            name='MA Color',
            line=dict(color='lime', width=3),
            showlegend=False
        ),
        row=3, col=1
    )

    # Add circle markers for trend changes (like PineScript shapes)
    trend_up_signals = result[(result['ma_short_term_xtrender'] > result['ma_short_term_xtrender'].shift(1)) &
                             (result['ma_short_term_xtrender'].shift(1) < result['ma_short_term_xtrender'].shift(2))]
    trend_down_signals = result[(result['ma_short_term_xtrender'] < result['ma_short_term_xtrender'].shift(1)) &
                               (result['ma_short_term_xtrender'].shift(1) > result['ma_short_term_xtrender'].shift(2))]

    fig.add_trace(
        go.Scatter(
            x=trend_up_signals.index,
            y=trend_up_signals['ma_short_term_xtrender'],
            mode='markers',
            marker=dict(symbol='circle', size=6, color='lime', line=dict(width=1, color='darkgreen')),
            name='Trend Up',
            showlegend=False
        ),
        row=3, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=trend_down_signals.index,
            y=trend_down_signals['ma_short_term_xtrender'],
            mode='markers',
            marker=dict(symbol='circle', size=6, color='red', line=dict(width=1, color='darkred')),
            name='Trend Down',
            showlegend=False
        ),
        row=3, col=1
    )

    # 4. Long-term Xtrender
    # Histogram bars
    long_colors = []
    for idx in result.index:
        val = result.loc[idx, 'long_term_xtrender']
        prev_val = result.loc[idx, 'long_term_xtrender'] if idx == result.index[0] else result.shift(1).loc[idx, 'long_term_xtrender']

        if val > 0:
            if val > prev_val:
                long_colors.append('lime')
            else:
                long_colors.append('#228B22')
        else:
            if val > prev_val:
                long_colors.append('red')
            else:
                long_colors.append('#8B0000')

    fig.add_trace(
        go.Bar(
            x=result.index,
            y=result['long_term_xtrender'],
            name='Long-term Xtrender',
            marker_color=long_colors,
            opacity=0.8,
            showlegend=False
        ),
        row=4, col=1
    )

    # Black shadow line
    fig.add_trace(
        go.Scatter(
            x=result.index,
            y=result['long_term_xtrender'],
            mode='lines',
            name='Long-term Shadow',
            line=dict(color='black', width=5),
            showlegend=False
        ),
        row=4, col=1
    )

    # Color line on top
    long_trend = result['long_term_xtrender'] > result['long_term_xtrender'].shift(1)
    long_ma_colors = ['lime' if x else 'red' for x in long_trend]
    fig.add_trace(
        go.Scatter(
            x=result.index,
            y=result['long_term_xtrender'],
            mode='lines',
            name='Long-term Color',
            line=dict(color='lime', width=3),
            showlegend=False
        ),
        row=4, col=1
    )

    # Update layout to match PineScript style
    fig.update_layout(
        title=dict(
            text=f'B-Xtrender @Puppytherapy - {symbol}',
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='black')
        ),
        height=1000,
        showlegend=False,
        xaxis_rangeslider_visible=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Update y-axes labels and ranges
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Oscillator", row=2, col=1)
    fig.update_yaxes(title_text="Shadow", row=3, col=1)
    fig.update_yaxes(title_text="Trend", row=4, col=1)

    # Set appropriate y-axis ranges for oscillator
    fig.update_yaxes(range=[-50, 50], row=2, col=1)
    fig.update_yaxes(range=[-50, 50], row=3, col=1)
    fig.update_yaxes(range=[-50, 50], row=4, col=1)

    # Add horizontal reference lines at 0
    for row in [2, 3, 4]:
        fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.5, row=row, col=1)

    # Save as HTML if requested
    if save_html:
        filename = f'bxtrender_panel_{symbol}.html'
        fig.write_html(filename)
        print(f"Panel visualization saved as {filename}")

    fig.show()

    # Print signal analysis
    print("\nSignal Analysis:")
    print(f"Total Buy Signals: {result['short_buy_signal'].sum()}")
    print(f"Total Sell Signals: {result['short_sell_signal'].sum()}")

    return fig, result


if __name__ == "__main__":
    # Run the multi-timeframe visualization with extended historical data
    print("Using 5 years weekly + 10 years monthly historical data for AAPL...")
    fig, results, entry_signals = create_bxtrender_multi_timeframe(symbol='AAPL', save_html=True)
