"""
Combined B-Xtrender + Fair Value Bands Strategy
================================================

ENTRY LOGIC:
------------
1. Monthly B-Xtrender closes with "light" color (increasing momentum)
   - Light Green: BX > 0 AND increasing
   - Light Red: BX < 0 AND increasing (bottoming signal)

2. Weekly B-Xtrender closes with "light" color in the NEXT month after monthly confirmation
   - Light Green: BX > 0 AND increasing
   - Light Red: BX < 0 AND increasing

→ ENTRY: When both conditions met (conservative, wait for closes)

EXIT LOGIC:
-----------
1. 100% Exit: Daily close ABOVE 2x upper Fair Value Band
2. 50% Exit: Weekly close ABOVE 1x upper Fair Value Band
3. Stop Loss: Weekly B-Xtrender closes "dark red" (BX < 0 AND decreasing)

→ All exits wait for candle CLOSE confirmation

Author: Combined Strategy System
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
from indicators.bxtrender import calculate_bxtrender
from indicators.fair_value_bands import calculate_fair_value_bands, FAIR_VALUE_PARAMS
from config import BX_TRENDER_PARAMS

def generate_combined_signals(symbol='AAPL', 
                              daily_period='2y',
                              weekly_period='5y',
                              monthly_period='10y'):
    """
    Generate combined B-Xtrender entry + Fair Value Bands exit signals.
    
    Args:
        symbol: Trading symbol
        daily_period: Historical period for daily data
        weekly_period: Historical period for weekly data
        monthly_period: Historical period for monthly data
        
    Returns:
        tuple: (figure, data_dict, signals_dict)
    """
    
    print(f"\n{'='*70}")
    print(f"COMBINED STRATEGY: {symbol}")
    print(f"{'='*70}\n")
    
    # ========================================================================
    # STEP 1: Load Data for All Timeframes
    # ========================================================================
    print("Loading data...")
    
    data_handler = DataHandler()
    
    # Daily data (for Fair Value Bands exits)
    # Load 10 years for proper band calculation, but we'll only display last 2 years
    daily_data_full = data_handler.get_data(symbol, period='10y', interval='1d')
    daily_data = daily_data_full  # Use full dataset for calculation
    print(f"✓ Loaded {len(daily_data)} daily bars (10y for proper FVB calculation)")
    
    # Weekly data (for B-Xtrender signals + FVB 50% exits)
    weekly_data = data_handler.get_data(symbol, period=weekly_period, interval='1wk')
    print(f"✓ Loaded {len(weekly_data)} weekly bars")
    
    # Monthly data (for B-Xtrender confirmation)
    monthly_data = data_handler.get_data(symbol, period=monthly_period, interval='1mo')
    print(f"✓ Loaded {len(monthly_data)} monthly bars")
    
    # ========================================================================
    # STEP 2: Calculate Indicators
    # ========================================================================
    print("\nCalculating indicators...")
    
    # B-Xtrender on weekly and monthly
    weekly_bx = calculate_bxtrender(weekly_data, **BX_TRENDER_PARAMS)
    print("✓ Weekly B-Xtrender calculated")
    
    monthly_bx = calculate_bxtrender(monthly_data, **BX_TRENDER_PARAMS)
    print("✓ Monthly B-Xtrender calculated")
    
    # Fair Value Bands on daily and weekly (use full historical data)
    daily_fvb = calculate_fair_value_bands(daily_data, **FAIR_VALUE_PARAMS)
    print("✓ Daily Fair Value Bands calculated")
    
    # Trim daily data to last 2 years for display (but keep full calculations)
    two_years_ago = daily_fvb.index[-1] - pd.DateOffset(years=2)
    daily_fvb_display = daily_fvb[daily_fvb.index >= two_years_ago]
    print(f"✓ Daily display trimmed to last 2 years ({len(daily_fvb_display)} bars)")
    
    weekly_fvb = calculate_fair_value_bands(weekly_data, **FAIR_VALUE_PARAMS)
    print("✓ Weekly Fair Value Bands calculated")
    
    # ========================================================================
    # STEP 3: Generate Entry Signals (B-Xtrender Logic)
    # ========================================================================
    print("\nGenerating entry signals...")
    
    entry_signals = []
    
    # Find favorable monthly closes (light colors = increasing)
    favorable_monthly = []
    
    for i in range(1, len(monthly_bx)):
        date = monthly_bx.index[i]
        bx_value = monthly_bx['short_term_xtrender'].iloc[i]
        prev_bx_value = monthly_bx['short_term_xtrender'].iloc[i-1]
        
        is_increasing = bx_value > prev_bx_value
        
        # Light Green: BX > 0 AND increasing
        # Light Red: BX < 0 AND increasing
        is_light = is_increasing
        
        if is_light:
            favorable_monthly.append({
                'monthly_close_date': date,
                'bx_value': bx_value,
                'is_green': bx_value > 0
            })
    
    print(f"✓ Found {len(favorable_monthly)} favorable monthly closes")
    
    # For each favorable monthly close, look for weekly signals in NEXT month
    for monthly_info in favorable_monthly:
        monthly_close_date = monthly_info['monthly_close_date']
        
        # Find the next monthly close date for the range
        monthly_idx = monthly_bx.index.get_loc(monthly_close_date)
        if monthly_idx + 1 < len(monthly_bx):
            next_monthly_date = monthly_bx.index[monthly_idx + 1]
        else:
            # If no next month, use end of data
            next_monthly_date = weekly_bx.index[-1]
        
        # Find weekly bars in the NEXT month (after monthly confirmation)
        weekly_in_range = weekly_bx[
            (weekly_bx.index > monthly_close_date) & 
            (weekly_bx.index <= next_monthly_date)
        ]
        
        # Check each weekly bar for light color close
        for weekly_date in weekly_in_range.index:
            weekly_idx = weekly_bx.index.get_loc(weekly_date)
            
            if weekly_idx > 0:
                weekly_bx_value = weekly_bx['short_term_xtrender'].iloc[weekly_idx]
                prev_weekly_bx = weekly_bx['short_term_xtrender'].iloc[weekly_idx - 1]
                
                is_weekly_increasing = weekly_bx_value > prev_weekly_bx
                
                # Light color = increasing
                if is_weekly_increasing:
                    entry_signals.append({
                        'date': weekly_date,
                        'price': weekly_bx['Close'].iloc[weekly_idx],
                        'weekly_bx': weekly_bx_value,
                        'monthly_date': monthly_close_date,
                        'monthly_bx': monthly_info['bx_value']
                    })
    
    print(f"✓ Found {len(entry_signals)} entry signals")
    
    # ========================================================================
    # STEP 4: Generate Exit Signals (Fair Value Bands)
    # ========================================================================
    print("\nGenerating exit signals...")
    
    exit_100_signals = []  # 100% exits (daily 2x band)
    exit_50_signals = []   # 50% exits (weekly 1x band)
    stop_loss_signals = [] # Stop loss (weekly BX dark red)
    
    # 100% Exit: Daily close above 2x upper band (check full dataset)
    for date in daily_fvb.index:
        close_price = daily_fvb.loc[date, 'Close']
        upper_2x = daily_fvb.loc[date, 'deviation_upper_2x']
        
        if pd.notna(upper_2x):
            if close_price > upper_2x:
                exit_100_signals.append({
                    'date': date,
                    'price': close_price,
                    'band_level': upper_2x,
                    'type': '100% Exit'
                })
    
    # 50% Exit: Weekly close above 1x upper band
    for date in weekly_fvb.index:
        close_price = weekly_fvb.loc[date, 'Close']
        upper_1x = weekly_fvb.loc[date, 'deviation_upper_1x']
        
        if pd.notna(upper_1x):
            if close_price > upper_1x:
                exit_50_signals.append({
                    'date': date,
                    'price': close_price,
                    'band_level': upper_1x,
                    'type': '50% Exit'
                })
    
    # Stop Loss: Weekly BX closes dark red (BX < 0 AND decreasing)
    for i in range(1, len(weekly_bx)):
        bx_value = weekly_bx['short_term_xtrender'].iloc[i]
        prev_bx = weekly_bx['short_term_xtrender'].iloc[i-1]
        
        is_dark_red = (bx_value < 0) and (bx_value < prev_bx)
        
        if is_dark_red:
            stop_loss_signals.append({
                'date': weekly_bx.index[i],
                'price': weekly_bx['Close'].iloc[i],
                'bx_value': bx_value,
                'type': 'Stop Loss'
            })
    
    print(f"✓ Found {len(exit_100_signals)} daily 2x exits (100%)")
    print(f"✓ Found {len(exit_50_signals)} weekly 1x exits (50%)")
    print(f"✓ Found {len(stop_loss_signals)} weekly BX stop losses")
    
    # ========================================================================
    # STEP 5: Create Visualization (3 Panels)
    # ========================================================================
    print("\nCreating visualization...")
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.08,
        subplot_titles=(
            f'{symbol} Daily Price + Fair Value Bands (100% Exit)',
            f'{symbol} Weekly Price + Fair Value Bands (50% Exit) + Entry Signals',
            f'{symbol} Weekly B-Xtrender Histogram (Entry & Stop Loss)'
        ),
        row_heights=[0.35, 0.35, 0.30]
    )
    
    # ====================================================================
    # PANEL 1: Daily Price + Fair Value Bands (100% Exits)
    # ====================================================================
    
    # Candlesticks (display only last 2 years)
    fig.add_trace(
        go.Candlestick(
            x=daily_fvb_display.index,
            open=daily_fvb_display['Open'],
            high=daily_fvb_display['High'],
            low=daily_fvb_display['Low'],
            close=daily_fvb_display['Close'],
            name='Daily Price',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Fair Value
    fig.add_trace(
        go.Scatter(
            x=daily_fvb_display.index,
            y=daily_fvb_display['fair_value'],
            mode='lines',
            name='Fair Value',
            line=dict(color='blue', width=1.5),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 1x Upper
    fig.add_trace(
        go.Scatter(
            x=daily_fvb_display.index,
            y=daily_fvb_display['deviation_upper_1x'],
            mode='lines',
            name='1x Upper',
            line=dict(color='rgb(196,177,101)', width=1.5, dash='dash'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 2x Upper
    fig.add_trace(
        go.Scatter(
            x=daily_fvb_display.index,
            y=daily_fvb_display['deviation_upper_2x'],
            mode='lines',
            name='2x Upper (100% Exit)',
            line=dict(color='rgb(255,107,107)', width=2, dash='dot'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 100% Exit Stars (filter to display range)
    if exit_100_signals:
        exit_100_display = [s for s in exit_100_signals if s['date'] >= two_years_ago]
        if exit_100_display:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in exit_100_display],
                    y=[s['price'] for s in exit_100_display],
                    mode='markers',
                    marker=dict(
                        symbol='star',
                        size=12,
                        color='red',
                        line=dict(width=2, color='darkred')
                    ),
                    text=[f"100% EXIT<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}" 
                          for s in exit_100_display],
                    hoverinfo='text',
                    name='100% Exit',
                    showlegend=True
                ),
                row=1, col=1
            )
    
    # ====================================================================
    # PANEL 2: Weekly Price + Fair Value Bands + Entry Signals
    # ====================================================================
    
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
    
    # Fair Value
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
    
    # 1x Upper
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
    
    # 2x Upper
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_2x'],
            mode='lines',
            name='2x Upper',
            line=dict(color='rgb(255,107,107)', width=2, dash='dot'),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Entry Signals (Green Stars)
    if entry_signals:
        fig.add_trace(
            go.Scatter(
                x=[s['date'] for s in entry_signals],
                y=[s['price'] for s in entry_signals],
                mode='markers',
                marker=dict(
                    symbol='star',
                    size=15,
                    color='lime',
                    line=dict(width=2, color='darkgreen')
                ),
                text=[f"ENTRY<br>W:{s['date'].strftime('%m/%d')}<br>M:{s['monthly_date'].strftime('%m/%d')}<br>${s['price']:.2f}" 
                      for s in entry_signals],
                hoverinfo='text',
                name='Entry Signal',
                showlegend=True
            ),
            row=2, col=1
        )
    
    # 50% Exit Stars
    if exit_50_signals:
        fig.add_trace(
            go.Scatter(
                x=[s['date'] for s in exit_50_signals],
                y=[s['price'] for s in exit_50_signals],
                mode='markers',
                marker=dict(
                    symbol='star',
                    size=12,
                    color='orange',
                    line=dict(width=2, color='darkorange')
                ),
                text=[f"50% EXIT<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}" 
                      for s in exit_50_signals],
                hoverinfo='text',
                name='50% Exit',
                showlegend=True
            ),
            row=2, col=1
        )
    
    # ====================================================================
    # PANEL 3: Weekly B-Xtrender Histogram (Entry + Stop Loss Signals)
    # ====================================================================
    
    # Determine colors for each bar
    colors = []
    for i in range(len(weekly_bx)):
        bx_value = weekly_bx['short_term_xtrender'].iloc[i]
        
        if i == 0:
            # First bar - use simple color
            if bx_value > 0:
                colors.append('rgba(0, 255, 0, 0.3)')  # Light green
            else:
                colors.append('rgba(255, 0, 0, 0.3)')  # Light red
        else:
            prev_bx = weekly_bx['short_term_xtrender'].iloc[i-1]
            is_increasing = bx_value > prev_bx
            
            if bx_value > 0:
                if is_increasing:
                    colors.append('rgba(0, 255, 0, 0.6)')  # Light green
                else:
                    colors.append('rgba(0, 100, 0, 0.6)')  # Dark green
            else:
                if is_increasing:
                    colors.append('rgba(255, 0, 0, 0.6)')  # Light red
                else:
                    colors.append('rgba(139, 0, 0, 0.6)')  # Dark red
    
    # Histogram
    fig.add_trace(
        go.Bar(
            x=weekly_bx.index,
            y=weekly_bx['short_term_xtrender'],
            marker=dict(color=colors),
            name='Weekly BX',
            showlegend=False,
            hovertemplate='%{x|%Y-%m-%d}<br>BX: %{y:.2f}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # Entry signal markers on histogram
    if entry_signals:
        entry_bx_values = []
        entry_dates = []
        for signal in entry_signals:
            idx = weekly_bx.index.get_loc(signal['date'])
            entry_bx_values.append(weekly_bx['short_term_xtrender'].iloc[idx])
            entry_dates.append(signal['date'])
        
        fig.add_trace(
            go.Scatter(
                x=entry_dates,
                y=entry_bx_values,
                mode='markers',
                marker=dict(
                    symbol='star',
                    size=12,
                    color='lime',
                    line=dict(width=2, color='darkgreen')
                ),
                name='Entry',
                showlegend=False
            ),
            row=3, col=1
        )
    
    # Stop Loss markers on histogram
    if stop_loss_signals:
        sl_bx_values = []
        sl_dates = []
        for signal in stop_loss_signals:
            idx = weekly_bx.index.get_loc(signal['date'])
            sl_bx_values.append(weekly_bx['short_term_xtrender'].iloc[idx])
            sl_dates.append(signal['date'])
        
        fig.add_trace(
            go.Scatter(
                x=sl_dates,
                y=sl_bx_values,
                mode='markers',
                marker=dict(
                    symbol='x',
                    size=12,
                    color='purple',
                    line=dict(width=3)
                ),
                text=[f"STOP LOSS<br>{s['date'].strftime('%Y-%m-%d')}<br>BX: {s['bx_value']:.2f}" 
                      for s in stop_loss_signals],
                hoverinfo='text',
                name='Stop Loss',
                showlegend=True
            ),
            row=3, col=1
        )
    
    # ====================================================================
    # Layout
    # ====================================================================
    
    fig.update_layout(
        title=dict(
            text=f'{symbol} - Combined B-Xtrender Entry + Fair Value Bands Exit Strategy<br>'
                 f'<sub>Green Stars = Entry | Red Stars = 100% Exit | Orange Stars = 50% Exit | Purple X = Stop Loss</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=14)
        ),
        height=1200,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Update axes
    fig.update_yaxes(title_text="Daily Price", row=1, col=1)
    fig.update_yaxes(title_text="Weekly Price", row=2, col=1)
    fig.update_yaxes(title_text="Weekly BX", row=3, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    
    # Save to HTML
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'combined_strategy_{symbol}_{timestamp}.html'
    fig.write_html(filename)
    print(f"\n✓ Chart saved as {filename}")
    
    # Also save as index.html for GitHub Pages
    fig.write_html('index.html')
    print(f"✓ Chart saved as index.html (for GitHub Pages)")
    
    # ========================================================================
    # STEP 6: Print Signal Summary
    # ========================================================================
    print(f"\n{'='*70}")
    print("SIGNAL SUMMARY")
    print(f"{'='*70}\n")
    
    print("🟢 ENTRY SIGNALS (B-Xtrender):")
    print("-" * 70)
    print(f"  Total entries: {len(entry_signals)}")
    if entry_signals:
        print(f"\n  Recent entries (last 5):")
        for signal in entry_signals[-5:]:
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (Monthly: {signal['monthly_date'].strftime('%Y-%m-%d')})")
    
    print(f"\n🔴 100% EXIT SIGNALS (Daily 2x Band):")
    print("-" * 70)
    print(f"  Total 100% exits: {len(exit_100_signals)}")
    if exit_100_signals:
        print(f"\n  Recent exits (last 5):")
        for signal in exit_100_signals[-5:]:
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (Band: ${signal['band_level']:.2f})")
    
    print(f"\n🟠 50% EXIT SIGNALS (Weekly 1x Band):")
    print("-" * 70)
    print(f"  Total 50% exits: {len(exit_50_signals)}")
    if exit_50_signals:
        print(f"\n  Recent exits (last 5):")
        for signal in exit_50_signals[-5:]:
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (Band: ${signal['band_level']:.2f})")
    
    print(f"\n🟣 STOP LOSS SIGNALS (Weekly BX Dark Red):")
    print("-" * 70)
    print(f"  Total stop losses: {len(stop_loss_signals)}")
    if stop_loss_signals:
        print(f"\n  Recent stop losses (last 5):")
        for signal in stop_loss_signals[-5:]:
            print(f"    {signal['date'].strftime('%Y-%m-%d')}: ${signal['price']:.2f} (BX: {signal['bx_value']:.2f})")
    
    print(f"\n{'='*70}")
    print("DATA RANGES")
    print(f"{'='*70}")
    print(f"Daily:   {daily_fvb.index[0].strftime('%Y-%m-%d')} to {daily_fvb.index[-1].strftime('%Y-%m-%d')}")
    print(f"Weekly:  {weekly_bx.index[0].strftime('%Y-%m-%d')} to {weekly_bx.index[-1].strftime('%Y-%m-%d')}")
    print(f"Monthly: {monthly_bx.index[0].strftime('%Y-%m-%d')} to {monthly_bx.index[-1].strftime('%Y-%m-%d')}")
    print(f"{'='*70}\n")
    
    fig.show()
    
    return fig, {
        'daily': daily_fvb,
        'weekly_price': weekly_fvb,
        'weekly_bx': weekly_bx,
        'monthly_bx': monthly_bx
    }, {
        'entries': entry_signals,
        'exit_100': exit_100_signals,
        'exit_50': exit_50_signals,
        'stop_loss': stop_loss_signals
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("COMBINED B-XTRENDER + FAIR VALUE BANDS STRATEGY")
    print("="*70)
    print("\nENTRY: Monthly + Weekly B-Xtrender light colors (increasing)")
    print("EXIT: Daily 2x band (100%) OR Weekly 1x band (50%)")
    print("STOP: Weekly B-Xtrender dark red (BX < 0 AND decreasing)")
    print("\n" + "="*70 + "\n")
    
    fig, data, signals = generate_combined_signals(
        symbol='AAPL',
        daily_period='2y',
        weekly_period='5y',
        monthly_period='10y'
    )

