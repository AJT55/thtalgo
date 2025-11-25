"""
Fair Value Bands Trading Signal Generator
==========================================

This script generates trading signals based purely on Fair Value Bands:
- Entry: When price is favorable (can be customized)
- 100% Exit: When DAILY closes above/below 2x deviation band
- 50% Exit: When WEEKLY closes above/below 1x deviation band

All signals are based on CLOSES (conservative approach).

Author: Fair Value Bands Signal System
"""

import sys
import os
sys.path.append('.')

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

from data.data_handler import DataHandler
from indicators.fair_value_bands import calculate_fair_value_bands, FAIR_VALUE_PARAMS
from config import DATA_PARAMS

def generate_fvb_signals(symbol='AAPL', 
                        daily_period='2y',
                        weekly_period='5y'):
    """
    Generate Fair Value Bands trading signals with multi-timeframe exits.
    
    Signal Logic:
    =============
    
    EXIT SIGNALS (based on CLOSES):
    --------------------------------
    100% EXIT: Daily close ABOVE 2x upper band OR BELOW 2x lower band
    50% EXIT: Weekly close ABOVE 1x upper band OR BELOW 1x lower band
    
    All signals wait for candle close confirmation (conservative).
    
    Args:
        symbol: Trading symbol
        daily_period: Historical period for daily data
        weekly_period: Historical period for weekly data
        
    Returns:
        tuple: (figure, daily_data, weekly_data, exit_signals)
    """
    
    print(f"\n{'='*60}")
    print(f"Fair Value Bands Signal Generator: {symbol}")
    print(f"{'='*60}\n")
    
    # ========================================================================
    # STEP 1: Load Data for Both Timeframes
    # ========================================================================
    print("Loading data...")
    
    data_handler = DataHandler()
    
    # Daily data
    daily_data = data_handler.get_data(symbol, period=daily_period, interval='1d')
    print(f"✓ Loaded {len(daily_data)} daily bars")
    
    # Weekly data
    weekly_data = data_handler.get_data(symbol, period=weekly_period, interval='1wk')
    print(f"✓ Loaded {len(weekly_data)} weekly bars")
    
    # ========================================================================
    # STEP 2: Calculate Fair Value Bands
    # ========================================================================
    print("\nCalculating Fair Value Bands...")
    
    daily_fvb = calculate_fair_value_bands(daily_data, **FAIR_VALUE_PARAMS)
    print("✓ Daily FVB calculated")
    
    weekly_fvb = calculate_fair_value_bands(weekly_data, **FAIR_VALUE_PARAMS)
    print("✓ Weekly FVB calculated")
    
    # ========================================================================
    # STEP 3: Generate Exit Signals (Close-Based)
    # ========================================================================
    print("\nGenerating exit signals...")
    
    exit_signals = {
        '100_percent': [],  # Daily 2x band exits
        '50_percent': []    # Weekly 1x band exits
    }
    
    # ----------------------------------------------------------------------
    # 100% EXIT SIGNALS (Daily 2x Deviation Bands)
    # ----------------------------------------------------------------------
    # Exit when daily candle CLOSES above upper 2x band OR below lower 2x band
    # ----------------------------------------------------------------------
    
    for date in daily_fvb.index:
        close_price = daily_fvb.loc[date, 'Close']
        upper_2x = daily_fvb.loc[date, 'deviation_upper_2x']
        lower_2x = daily_fvb.loc[date, 'deviation_lower_2x']
        
        # Check if close is outside 2x bands
        if pd.notna(upper_2x) and pd.notna(lower_2x):
            if close_price > upper_2x:
                # LONG EXIT - Price closed above upper 2x band
                exit_signals['100_percent'].append({
                    'date': date,
                    'price': close_price,
                    'type': 'LONG_EXIT',
                    'band_level': upper_2x,
                    'timeframe': 'Daily',
                    'band_type': '2x Upper'
                })
            elif close_price < lower_2x:
                # SHORT EXIT - Price closed below lower 2x band
                exit_signals['100_percent'].append({
                    'date': date,
                    'price': close_price,
                    'type': 'SHORT_EXIT',
                    'band_level': lower_2x,
                    'timeframe': 'Daily',
                    'band_type': '2x Lower'
                })
    
    # ----------------------------------------------------------------------
    # 50% EXIT SIGNALS (Weekly 1x Deviation Bands)
    # ----------------------------------------------------------------------
    # Exit when weekly candle CLOSES above upper 1x band OR below lower 1x band
    # ----------------------------------------------------------------------
    
    for date in weekly_fvb.index:
        close_price = weekly_fvb.loc[date, 'Close']
        upper_1x = weekly_fvb.loc[date, 'deviation_upper_1x']
        lower_1x = weekly_fvb.loc[date, 'deviation_lower_1x']
        
        # Check if close is outside 1x bands
        if pd.notna(upper_1x) and pd.notna(lower_1x):
            if close_price > upper_1x:
                # LONG EXIT - Price closed above upper 1x band
                exit_signals['50_percent'].append({
                    'date': date,
                    'price': close_price,
                    'type': 'LONG_EXIT',
                    'band_level': upper_1x,
                    'timeframe': 'Weekly',
                    'band_type': '1x Upper'
                })
            elif close_price < lower_1x:
                # SHORT EXIT - Price closed below lower 1x band
                exit_signals['50_percent'].append({
                    'date': date,
                    'price': close_price,
                    'type': 'SHORT_EXIT',
                    'band_level': lower_1x,
                    'timeframe': 'Weekly',
                    'band_type': '1x Lower'
                })
    
    print(f"\n✓ Found {len(exit_signals['100_percent'])} Daily 2x band exits (100%)")
    print(f"✓ Found {len(exit_signals['50_percent'])} Weekly 1x band exits (50%)")
    
    # ========================================================================
    # STEP 4: Create Visualization
    # ========================================================================
    print("\nCreating visualization...")
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.1,
        subplot_titles=(
            f'{symbol} Daily Price with Fair Value Bands - 100% Exit Signals (2x)',
            f'{symbol} Weekly Price with Fair Value Bands - 50% Exit Signals (1x)'
        ),
        row_heights=[0.5, 0.5]
    )
    
    # ----------------------------------------------------------------------
    # Daily Chart (Top Panel)
    # ----------------------------------------------------------------------
    
    # Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=daily_fvb.index,
            open=daily_fvb['Open'],
            high=daily_fvb['High'],
            low=daily_fvb['Low'],
            close=daily_fvb['Close'],
            name='Daily Price',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Fair Value Basis
    fig.add_trace(
        go.Scatter(
            x=daily_fvb.index,
            y=daily_fvb['fair_value'],
            mode='lines',
            name='Fair Value',
            line=dict(color='blue', width=1.5),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 1x Deviation Bands
    fig.add_trace(
        go.Scatter(
            x=daily_fvb.index,
            y=daily_fvb['deviation_upper_1x'],
            mode='lines',
            name='1x Upper',
            line=dict(color='rgb(196,177,101)', width=1.5, dash='dash'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=daily_fvb.index,
            y=daily_fvb['deviation_lower_1x'],
            mode='lines',
            name='1x Lower',
            line=dict(color='rgb(196,177,101)', width=1.5, dash='dash'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 2x Deviation Bands (for 100% exit)
    fig.add_trace(
        go.Scatter(
            x=daily_fvb.index,
            y=daily_fvb['deviation_upper_2x'],
            mode='lines',
            name='2x Upper (100% Exit)',
            line=dict(color='rgb(255,107,107)', width=2, dash='dot'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=daily_fvb.index,
            y=daily_fvb['deviation_lower_2x'],
            mode='lines',
            name='2x Lower (100% Exit)',
            line=dict(color='rgb(255,107,107)', width=2, dash='dot'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 100% Exit Signals (Daily 2x band)
    if exit_signals['100_percent']:
        long_exits_100 = [s for s in exit_signals['100_percent'] if s['type'] == 'LONG_EXIT']
        short_exits_100 = [s for s in exit_signals['100_percent'] if s['type'] == 'SHORT_EXIT']
        
        if long_exits_100:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in long_exits_100],
                    y=[s['price'] for s in long_exits_100],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=15,
                        color='red',
                        line=dict(width=2, color='darkred')
                    ),
                    text=[f"100% EXIT<br>{s['date'].strftime('%Y-%m-%d')}<br>Price: ${s['price']:.2f}" 
                          for s in long_exits_100],
                    hoverinfo='text',
                    name='100% Long Exit',
                    showlegend=True
                ),
                row=1, col=1
            )
        
        if short_exits_100:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in short_exits_100],
                    y=[s['price'] for s in short_exits_100],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=15,
                        color='green',
                        line=dict(width=2, color='darkgreen')
                    ),
                    text=[f"100% EXIT<br>{s['date'].strftime('%Y-%m-%d')}<br>Price: ${s['price']:.2f}" 
                          for s in short_exits_100],
                    hoverinfo='text',
                    name='100% Short Exit',
                    showlegend=True
                ),
                row=1, col=1
            )
    
    # ----------------------------------------------------------------------
    # Weekly Chart (Bottom Panel)
    # ----------------------------------------------------------------------
    
    # Candlesticks
    fig.add_trace(
        go.Candlestick(
            x=weekly_fvb.index,
            open=weekly_fvb['Open'],
            high=weekly_fvb['High'],
            low=weekly_fvb['Low'],
            close=weekly_fvb['Close'],
            name='Weekly Price',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Fair Value Basis
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['fair_value'],
            mode='lines',
            name='Fair Value',
            line=dict(color='blue', width=1.5),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 1x Deviation Bands (for 50% exit)
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_1x'],
            mode='lines',
            name='1x Upper (50% Exit)',
            line=dict(color='rgb(196,177,101)', width=1.5, dash='dash'),
            showlegend=True
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_lower_1x'],
            mode='lines',
            name='1x Lower (50% Exit)',
            line=dict(color='rgb(196,177,101)', width=1.5, dash='dash'),
            showlegend=True
        ),
        row=2, col=1
    )
    
    # 2x Deviation Bands (for reference on weekly)
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_2x'],
            mode='lines',
            name='2x Upper',
            line=dict(color='rgb(255,107,107)', width=2, dash='dot'),
            showlegend=True
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_lower_2x'],
            mode='lines',
            name='2x Lower',
            line=dict(color='rgb(255,107,107)', width=2, dash='dot'),
            showlegend=True
        ),
        row=2, col=1
    )
    
    # 50% Exit Signals (Weekly 1x band)
    if exit_signals['50_percent']:
        long_exits_50 = [s for s in exit_signals['50_percent'] if s['type'] == 'LONG_EXIT']
        short_exits_50 = [s for s in exit_signals['50_percent'] if s['type'] == 'SHORT_EXIT']
        
        if long_exits_50:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in long_exits_50],
                    y=[s['price'] for s in long_exits_50],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=15,
                        color='orange',
                        line=dict(width=2, color='darkorange')
                    ),
                    text=[f"50% EXIT<br>{s['date'].strftime('%Y-%m-%d')}<br>Price: ${s['price']:.2f}" 
                          for s in long_exits_50],
                    hoverinfo='text',
                    name='50% Long Exit',
                    showlegend=True
                ),
                row=2, col=1
            )
        
        if short_exits_50:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in short_exits_50],
                    y=[s['price'] for s in short_exits_50],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=15,
                        color='lightblue',
                        line=dict(width=2, color='blue')
                    ),
                    text=[f"50% EXIT<br>{s['date'].strftime('%Y-%m-%d')}<br>Price: ${s['price']:.2f}" 
                          for s in short_exits_50],
                    hoverinfo='text',
                    name='50% Short Exit',
                    showlegend=True
                ),
                row=2, col=1
            )
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'{symbol} - Fair Value Bands Exit Signals<br>'
                 f'<sub>Red Stars = 100% Exit (Daily 2x) | Orange Stars = 50% Exit (Weekly 1x)</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=14)
        ),
        height=900,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    fig.update_yaxes(title_text="Daily Price", row=1, col=1)
    fig.update_yaxes(title_text="Weekly Price", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    
    # Save to HTML
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'fvb_signals_{symbol}_{timestamp}.html'
    fig.write_html(filename)
    print(f"\n✓ Chart saved as {filename}")
    
    # Also save as index.html for GitHub Pages
    fig.write_html('index.html')
    print(f"✓ Chart saved as index.html (for GitHub Pages)")
    
    # ========================================================================
    # STEP 5: Print Signal Summary
    # ========================================================================
    print(f"\n{'='*60}")
    print("EXIT SIGNAL SUMMARY")
    print(f"{'='*60}\n")
    
    # 100% Exits
    print("📍 100% EXIT SIGNALS (Daily 2x Bands):")
    print("-" * 60)
    
    long_100 = [s for s in exit_signals['100_percent'] if s['type'] == 'LONG_EXIT']
    short_100 = [s for s in exit_signals['100_percent'] if s['type'] == 'SHORT_EXIT']
    
    print(f"  Long Exits (above upper 2x): {len(long_100)}")
    if long_100:
        for signal in long_100[-5:]:  # Show last 5
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (Band: ${signal['band_level']:.2f})")
    
    print(f"\n  Short Exits (below lower 2x): {len(short_100)}")
    if short_100:
        for signal in short_100[-5:]:  # Show last 5
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (Band: ${signal['band_level']:.2f})")
    
    # 50% Exits
    print(f"\n📍 50% EXIT SIGNALS (Weekly 1x Bands):")
    print("-" * 60)
    
    long_50 = [s for s in exit_signals['50_percent'] if s['type'] == 'LONG_EXIT']
    short_50 = [s for s in exit_signals['50_percent'] if s['type'] == 'SHORT_EXIT']
    
    print(f"  Long Exits (above upper 1x): {len(long_50)}")
    if long_50:
        for signal in long_50[-5:]:  # Show last 5
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (Band: ${signal['band_level']:.2f})")
    
    print(f"\n  Short Exits (below lower 1x): {len(short_50)}")
    if short_50:
        for signal in short_50[-5:]:  # Show last 5
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (Band: ${signal['band_level']:.2f})")
    
    print(f"\n{'='*60}")
    print("STATISTICS")
    print(f"{'='*60}\n")
    
    print(f"Daily Data Range: {daily_fvb.index[0].strftime('%Y-%m-%d')} to {daily_fvb.index[-1].strftime('%Y-%m-%d')}")
    print(f"Weekly Data Range: {weekly_fvb.index[0].strftime('%Y-%m-%d')} to {weekly_fvb.index[-1].strftime('%Y-%m-%d')}")
    print(f"\nTotal 100% Exits: {len(exit_signals['100_percent'])}")
    print(f"Total 50% Exits: {len(exit_signals['50_percent'])}")
    
    fig.show()
    
    return fig, daily_fvb, weekly_fvb, exit_signals


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FAIR VALUE BANDS - EXIT SIGNAL GENERATOR")
    print("="*60)
    print("\nExit Strategy:")
    print("  • 100% Exit: Daily close breaks 2x deviation band")
    print("  • 50% Exit: Weekly close breaks 1x deviation band")
    print("  • All signals wait for candle CLOSE confirmation")
    print("\n" + "="*60 + "\n")
    
    fig, daily_data, weekly_data, exit_signals = generate_fvb_signals(
        symbol='AAPL',
        daily_period='2y',
        weekly_period='5y'
    )

