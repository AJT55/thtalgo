"""
Combined Strategy Backtest - ALL PANELS
========================================

Comprehensive visualization with 6 panels:
1. Daily Price + Bands (100% Exits)
2. Weekly Price + Bands (Visualization of levels)
3. Weekly Price + Actual Trades Only (Clean view)
4. Weekly B-Xtrender
5. Monthly B-Xtrender
6. Equity Curve

Author: Combined Chart
"""

import sys
sys.path.append('.')

from backtest_combined_strategy import run_backtest
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def create_all_panels_chart(symbol='AAPL'):
    """
    Create a single chart with ALL panels on one page.
    """
    
    print("\n" + "="*70)
    print("GENERATING ALL-IN-ONE CHART")
    print("="*70 + "\n")
    
    # Run backtest to get trades
    fig_full, trades, stats = run_backtest(symbol, 'max', '10y', '10y')
    
    # Get data for visualization
    from data.data_handler import DataHandler
    from indicators.bxtrender import calculate_bxtrender
    from indicators.fair_value_bands import calculate_fair_value_bands, FAIR_VALUE_PARAMS
    from config import BX_TRENDER_PARAMS
    
    dh = DataHandler()
    daily = dh.get_data(symbol, period='max', interval='1d')
    weekly = dh.get_data(symbol, period='10y', interval='1wk')
    monthly = dh.get_data(symbol, period='10y', interval='1mo')
    
    daily_fvb = calculate_fair_value_bands(daily, **FAIR_VALUE_PARAMS)
    weekly_fvb = calculate_fair_value_bands(weekly, **FAIR_VALUE_PARAMS)
    weekly_bx = calculate_bxtrender(weekly, **BX_TRENDER_PARAMS)
    monthly_bx = calculate_bxtrender(monthly, **BX_TRENDER_PARAMS)
    
    # Trim daily to 10 years
    ten_years_ago = daily_fvb.index[-1] - pd.DateOffset(years=10)
    daily_display = daily_fvb[daily_fvb.index >= ten_years_ago]
    
    print(f"\nCreating 6-panel visualization...")
    
    # ====================================================================
    # Create Chart with 6 Rows
    # ====================================================================
    
    fig = make_subplots(
        rows=6, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.04,
        subplot_titles=(
            f'{symbol} Daily Price + Bands (100% Exits)',
            f'{symbol} Weekly Price + Bands (Levels)',
            f'{symbol} Weekly Price + Actual Trades Only',
            f'{symbol} Weekly B-Xtrender',
            f'{symbol} Monthly B-Xtrender',
            'Account Equity ($)'
        ),
        row_heights=[0.20, 0.20, 0.20, 0.15, 0.15, 0.10]
    )
    
    # ====================================================================
    # PANEL 1: Daily Price + FVB + 100% Exits
    # ====================================================================
    
    fig.add_trace(
        go.Candlestick(
            x=daily_display.index,
            open=daily_display['Open'],
            high=daily_display['High'],
            low=daily_display['Low'],
            close=daily_display['Close'],
            name='Daily Price',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Fair Value
    fig.add_trace(
        go.Scatter(
            x=daily_display.index,
            y=daily_display['fair_value'],
            mode='lines',
            name='Fair Value',
            line=dict(color='blue', width=1),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 1x Upper
    fig.add_trace(
        go.Scatter(
            x=daily_display.index,
            y=daily_display['deviation_upper_1x'],
            mode='lines',
            name='1x Upper',
            line=dict(color='rgb(196,177,101)', width=1, dash='dash'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # 2x Upper
    fig.add_trace(
        go.Scatter(
            x=daily_display.index,
            y=daily_display['deviation_upper_2x'],
            mode='lines',
            name='2x Upper (100%)',
            line=dict(color='rgb(255,107,107)', width=1.5, dash='dot'),
            showlegend=True
        ),
        row=1, col=1
    )
    
    # Show 100% exits
    exits_100 = []
    for i, trade in enumerate(trades, 1):
        for exit_info in trade.exits:
            if exit_info['reason'] == '100% Exit (Daily 2x)':
                exits_100.append({'date': exit_info['date'], 'price': exit_info['price'], 'trade_num': i})
    
    if exits_100:
        fig.add_trace(
            go.Scatter(
                x=[e['date'] for e in exits_100],
                y=[e['price'] for e in exits_100],
                mode='markers+text',
                marker=dict(symbol='star', size=12, color='red', line=dict(width=2, color='darkred')),
                text=[f"#{e['trade_num']}" for e in exits_100],
                textposition='top center',
                textfont=dict(size=9, color='darkred', family='Arial Black'),
                hovertext=[f"100% EXIT #{e['trade_num']}<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for e in exits_100],
                hoverinfo='text',
                name='100% Exit',
                showlegend=True
            ),
            row=1, col=1
        )
        
    # ====================================================================
    # PANEL 2: Weekly Price + Bands + All Trade Events
    # ====================================================================
    
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
    
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['fair_value'],
            mode='lines',
            name='Fair Value',
            line=dict(color='blue', width=1),
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_1x'],
            mode='lines',
            name='1x Upper (50%)',
            line=dict(color='rgb(196,177,101)', width=1.5, dash='dash'),
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_2x'],
            mode='lines',
            name='2x Upper',
            line=dict(color='rgb(255,107,107)', width=1, dash='dot'),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Add ALL trade events to weekly bands panel
    if trades:
        # Entries
        fig.add_trace(
            go.Scatter(
                x=[t.entry_date for t in trades],
                y=[t.entry_price for t in trades],
                mode='markers',
                marker=dict(symbol='star', size=15, color='lime', line=dict(width=2, color='darkgreen')),
                text=[f"ENTRY #{i+1}<br>{t.entry_date.strftime('%Y-%m-%d')}<br>${t.entry_price:.2f}" for i, t in enumerate(trades)],
                hoverinfo='text',
                name='Entry',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # 50% Exits
        exits_50_weekly = [{'date': e['date'], 'price': e['price'], 'trade_num': i+1} 
                           for i, t in enumerate(trades) for e in t.exits if '50%' in e['reason']]
        if exits_50_weekly:
            fig.add_trace(
                go.Scatter(
                    x=[e['date'] for e in exits_50_weekly],
                    y=[e['price'] for e in exits_50_weekly],
                    mode='markers',
                    marker=dict(symbol='star', size=12, color='orange', line=dict(width=2, color='darkorange')),
                    text=[f"50% EXIT #{e['trade_num']}<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for e in exits_50_weekly],
                    hoverinfo='text',
                    name='50% Exit',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # 100% Exits on weekly panel
        exits_100_weekly = [{'date': e['date'], 'price': e['price'], 'trade_num': i+1} 
                            for i, t in enumerate(trades) for e in t.exits if '100%' in e['reason']]
        if exits_100_weekly:
            fig.add_trace(
                go.Scatter(
                    x=[e['date'] for e in exits_100_weekly],
                    y=[e['price'] for e in exits_100_weekly],
                    mode='markers',
                    marker=dict(symbol='star', size=12, color='red', line=dict(width=2, color='darkred')),
                    text=[f"100% EXIT #{e['trade_num']}<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for e in exits_100_weekly],
                    hoverinfo='text',
                    name='100% Exit',
                    showlegend=False
                ),
                row=2, col=1
            )
            
        # Re-entries on weekly panel
        reentries_weekly = [{'date': r['date'], 'price': r['price'], 'trade_num': i+1} 
                            for i, t in enumerate(trades) for r in t.exits if r['percent'] < 0]
        if reentries_weekly:
            fig.add_trace(
                go.Scatter(
                    x=[r['date'] for r in reentries_weekly],
                    y=[r['price'] for r in reentries_weekly],
                    mode='markers',
                    marker=dict(symbol='diamond', size=12, color='cyan', line=dict(width=2, color='blue')),
                    text=[f"RE-ENTRY #{r['trade_num']}<br>{r['date'].strftime('%Y-%m-%d')}<br>${r['price']:.2f}" for r in reentries_weekly],
                    hoverinfo='text',
                    name='Re-Entry',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # Stop Losses on weekly panel
        stops_weekly = [{'date': s['date'], 'price': s['price'], 'trade_num': i+1} 
                        for i, t in enumerate(trades) for s in t.exits if 'Stop Loss' in s['reason']]
        if stops_weekly:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in stops_weekly],
                    y=[s['price'] for s in stops_weekly],
                    mode='markers',
                    marker=dict(symbol='x', size=12, color='purple', line=dict(width=3)),
                    text=[f"STOP #{s['trade_num']}<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}" for s in stops_weekly],
                    hoverinfo='text',
                    name='Stop Loss',
                    showlegend=False
                ),
                row=2, col=1
            )
    
    # ====================================================================
    # PANEL 3: Weekly Price + ACTUAL TRADES ONLY (No Bands)
    # ====================================================================
    
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
        row=3, col=1
    )
    
    # Trades with numbers
    if trades:
        # Separate completed and active trades
        completed = [t for t in trades if t.is_closed]
        active = [t for t in trades if not t.is_closed]
        
        # Completed Entries
        if completed:
            completed_indices = [i+1 for i, t in enumerate(trades) if t.is_closed]
            fig.add_trace(
                go.Scatter(
                    x=[t.entry_date for t in completed],
                    y=[t.entry_price for t in completed],
                    mode='markers+text',
                    marker=dict(symbol='star', size=15, color='lime', line=dict(width=2, color='darkgreen')),
                    text=[f"#{completed_indices[i]}" for i in range(len(completed))],
                    textposition='top center',
                    textfont=dict(size=10, color='darkgreen', family='Arial Black'),
                    hovertext=[f"ENTRY #{completed_indices[i]}<br>{t.entry_date.strftime('%Y-%m-%d')}<br>${t.entry_price:.2f}" for i, t in enumerate(completed)],
                    hoverinfo='text',
                    name='Entry (Closed)',
                    showlegend=True
                ),
                row=3, col=1
            )
        
        # Active Entries (different color)
        if active:
            active_indices = [i+1 for i, t in enumerate(trades) if not t.is_closed]
            fig.add_trace(
                go.Scatter(
                    x=[t.entry_date for t in active],
                    y=[t.entry_price for t in active],
                    mode='markers+text',
                    marker=dict(symbol='star', size=15, color='gold', line=dict(width=2, color='orange')),
                    text=[f"#{active_indices[i]}" for i in range(len(active))],
                    textposition='top center',
                    textfont=dict(size=10, color='orange', family='Arial Black'),
                    hovertext=[f"ENTRY #{active_indices[i]} (ACTIVE)<br>{t.entry_date.strftime('%Y-%m-%d')}<br>${t.entry_price:.2f}" for i, t in enumerate(active)],
                    hoverinfo='text',
                    name='Entry (Active)',
                    showlegend=True
                ),
                row=3, col=1
            )
        
        # 50% Exits
        exits_50 = [{'date': e['date'], 'price': e['price'], 'trade_num': i+1} 
                    for i, t in enumerate(trades) for e in t.exits if '50%' in e['reason']]
        if exits_50:
            fig.add_trace(
                go.Scatter(
                    x=[e['date'] for e in exits_50],
                    y=[e['price'] for e in exits_50],
                    mode='markers+text',
                    marker=dict(symbol='star', size=12, color='orange', line=dict(width=2, color='darkorange')),
                    text=[f"#{e['trade_num']}" for e in exits_50],
                    textposition='top center',
                    textfont=dict(size=9, color='darkorange', family='Arial Black'),
                    hovertext=[f"50% EXIT #{e['trade_num']}<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for e in exits_50],
                    hoverinfo='text',
                    name='50% Exit',
                    showlegend=True
                ),
                row=3, col=1
            )
            
        # Re-entries
        reentries = [{'date': r['date'], 'price': r['price'], 'trade_num': i+1} 
                     for i, t in enumerate(trades) for r in t.exits if r['percent'] < 0]
        if reentries:
            fig.add_trace(
                go.Scatter(
                    x=[r['date'] for r in reentries],
                    y=[r['price'] for r in reentries],
                    mode='markers+text',
                    marker=dict(symbol='diamond', size=12, color='cyan', line=dict(width=2, color='blue')),
                    text=[f"#{r['trade_num']}" for r in reentries],
                    textposition='top center',
                    textfont=dict(size=9, color='blue', family='Arial Black'),
                    hovertext=[f"RE-ENTRY #{r['trade_num']}<br>{r['date'].strftime('%Y-%m-%d')}<br>${r['price']:.2f}" for r in reentries],
                    hoverinfo='text',
                    name='Re-Entry +50%',
                    showlegend=True
                ),
                row=3, col=1
            )
        
        # Stop Losses
        stops = [{'date': s['date'], 'price': s['price'], 'trade_num': i+1} 
                 for i, t in enumerate(trades) for s in t.exits if 'Stop Loss' in s['reason']]
        if stops:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in stops],
                    y=[s['price'] for s in stops],
                    mode='markers+text',
                    marker=dict(symbol='x', size=12, color='purple', line=dict(width=3)),
                    text=[f"#{s['trade_num']}" for s in stops],
                    textposition='bottom center',
                    textfont=dict(size=9, color='purple', family='Arial Black'),
                    hovertext=[f"STOP #{s['trade_num']}<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}" for s in stops],
                    hoverinfo='text',
                    name='Stop Loss',
                    showlegend=True
                ),
                row=3, col=1
            )
    
    # ====================================================================
    # PANEL 4: Weekly B-Xtrender
    # ====================================================================
    
    weekly_colors = []
    for i in range(len(weekly_bx)):
        bx = weekly_bx['short_term_xtrender'].iloc[i]
        if i == 0:
            color = 'rgba(0,255,0,0.6)' if bx > 0 else 'rgba(255,0,0,0.6)'
        else:
            prev_bx = weekly_bx['short_term_xtrender'].iloc[i-1]
            is_increasing = bx > prev_bx
            if bx > 0:
                color = 'rgba(0,255,0,0.7)' if is_increasing else 'rgba(0,100,0,0.7)'
            else:
                color = 'rgba(255,100,100,0.7)' if is_increasing else 'rgba(139,0,0,0.7)'
        weekly_colors.append(color)
    
    fig.add_trace(
        go.Bar(
            x=weekly_bx.index,
            y=weekly_bx['short_term_xtrender'],
            marker=dict(color=weekly_colors),
            name='Weekly BX',
            showlegend=False
        ),
        row=4, col=1
    )
    
    # Mark entries
    if trades:
        entry_bx_vals = []
        for trade in trades:
            idx = weekly_bx.index.get_loc(trade.entry_date)
            entry_bx_vals.append(weekly_bx['short_term_xtrender'].iloc[idx])
        
        fig.add_trace(
            go.Scatter(
                x=[t.entry_date for t in trades],
                y=entry_bx_vals,
                mode='markers',
                marker=dict(symbol='star', size=12, color='lime', line=dict(width=2, color='darkgreen')),
                showlegend=False
            ),
            row=4, col=1
        )
    
    # ====================================================================
    # PANEL 5: Monthly B-Xtrender
    # ====================================================================
    
    monthly_colors = []
    monthly_display_dates = []
    monthly_hover = []
    
    for i in range(len(monthly_bx)):
        bx = monthly_bx['short_term_xtrender'].iloc[i]
        yf_index = monthly_bx.index[i]
        
        # DISPLAY date = actual month represented (shift -1 month from yfinance index)
        display_date = yf_index - pd.DateOffset(months=1)
        monthly_display_dates.append(display_date)
        
        if i == 0:
            color = 'rgba(0,255,0,0.6)' if bx > 0 else 'rgba(255,0,0,0.6)'
            color_name = 'Light Green' if bx > 0 else 'Light Red'
            prev_bx = 0
        else:
            prev_bx = monthly_bx['short_term_xtrender'].iloc[i-1]
            is_increasing = bx > prev_bx
            if bx > 0:
                color = 'rgba(0,255,0,0.7)' if is_increasing else 'rgba(0,100,0,0.7)'
                color_name = 'Light Green' if is_increasing else 'Dark Green'
            else:
                color = 'rgba(255,100,100,0.7)' if is_increasing else 'rgba(139,0,0,0.7)'
                color_name = 'Light Red' if is_increasing else 'Dark Red'
        
        monthly_colors.append(color)
        monthly_hover.append(
            f"<b>{display_date.strftime('%B %Y')}</b><br>"
            f"BX: {bx:.2f}<br>"
            f"Prev: {prev_bx:.2f}<br>"
            f"Color: {color_name}<br>"
            f"(YF Index: {yf_index.strftime('%Y-%m-%d')})"
        )
    
    fig.add_trace(
        go.Bar(
            x=monthly_display_dates,  # Use shifted dates for DISPLAY
            y=monthly_bx['short_term_xtrender'],
            marker=dict(color=monthly_colors),
            name='Monthly BX',
            showlegend=False,
            hovertext=monthly_hover,
            hoverinfo='text'
        ),
        row=5, col=1
    )
    
    # ====================================================================
    # PANEL 6: Equity Curve (in Dollars)
    # ====================================================================
    
    if trades:
        equity_curve = []
        cumulative_pnl_dollars = 0
        equity_dates = []
        starting_capital = trades[0].capital_allocated if trades else 10000
        
        # Start with initial capital
        equity_dates.append(trades[0].entry_date if trades else pd.Timestamp.now())
        equity_curve.append(starting_capital)
        
        for trade in trades:
            if trade.exits:
                cumulative_pnl_dollars += trade.calculate_pnl_dollars()
                current_equity = starting_capital + cumulative_pnl_dollars
                equity_curve.append(current_equity)
                # Use last exit date for this trade
                equity_dates.append(max([e['date'] for e in trade.exits]))
        
        fig.add_trace(
            go.Scatter(
                x=equity_dates,
                y=equity_curve,
                mode='lines+markers',
                name='Equity',
                line=dict(color='green', width=2),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(0,255,0,0.1)',
                showlegend=False
            ),
            row=6, col=1
        )
        
        fig.add_hline(y=starting_capital, line_dash="dash", line_color="gray", row=6, col=1)
    
    # Count active vs completed
    completed_count = len([t for t in trades if t.is_closed])
    active_count = len([t for t in trades if not t.is_closed])
    
    # Layout
    title_text = f'{symbol} - ALL-IN-ONE STRATEGY VIEW<br>'
    if stats:
        title_text += f'<sub>${stats["starting_capital"]:,.0f} → ${stats["final_capital"]:,.0f} | P&L: ${stats["total_pnl_dollars"]:+,.2f} ({stats["total_pnl"]:+.1f}%) | Completed: {completed_count} | Active: {active_count} | Win Rate: {stats["win_rate"]:.1f}%</sub>'
    else:
        title_text += f'<sub>Total Trades: {len(trades)} (All Active)</sub>'
    
    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor='center'
        ),
        height=2000,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        xaxis4_rangeslider_visible=False,
        xaxis5_rangeslider_visible=False,
        xaxis6_rangeslider_visible=False
    )
    
    # ====================================================================
    # CREATE TRADE TABLE
    # ====================================================================
    
    trade_table_html = """
    <div style="max-width: 1600px; margin: 40px auto; padding: 20px; font-family: Arial, sans-serif;">
        <h2 style="text-align: center; color: #333; margin-bottom: 30px;">📊 TRADE LOG</h2>
        <table style="width: 100%; border-collapse: collapse; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background-color: #2c3e50; color: white;">
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Trade #</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Entry Date</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Entry Price</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: left;">Exit Events</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">P&L ($)</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">P&L (%)</th>
                    <th style="padding: 12px; border: 1px solid #ddd; text-align: center;">Duration</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for i, trade in enumerate(trades, 1):
        pnl = trade.calculate_pnl()
        pnl_color = 'green' if pnl > 0 else 'red' if pnl < 0 else 'gray'
        
        # Check if trade is active
        is_active = not trade.is_closed
        row_bg = '#fffacd' if is_active else ('#f9f9f9' if i % 2 == 0 else 'white')  # Yellow highlight for active
        
        # Build exit events column
        exit_events = ""
        if is_active and not trade.exits:
            exit_events = '<div style="margin: 4px 0; padding: 4px 8px; background-color: rgba(255,215,0,0.3); border-radius: 4px;"><strong style="color: #b8860b;">🔄 ACTIVE</strong>: Position still open</div>'
        elif is_active:
            for exit_info in trade.exits:
                if exit_info['percent'] < 0:
                    # Re-entry
                    exit_events += f"""
                    <div style="margin: 4px 0; padding: 4px 8px; background-color: rgba(0,255,0,0.1); border-radius: 4px;">
                        <strong style="color: green;">+50% RE-ENTRY</strong>: 
                        {exit_info['date'].strftime('%Y-%m-%d')} @ ${exit_info['price']:.2f}
                    </div>
                    """
                else:
                    exit_type = "50%" if "50%" in exit_info['reason'] else "100%" if "100%" in exit_info['reason'] else "SL"
                    exit_color = 'orange' if exit_type == "50%" else 'red' if exit_type == "100%" else 'purple'
                    exit_events += f"""
                    <div style="margin: 4px 0; padding: 4px 8px; background-color: rgba(0,0,0,0.05); border-radius: 4px;">
                        <strong style="color: {exit_color};">{exit_type}</strong>: 
                        {exit_info['date'].strftime('%Y-%m-%d')} @ ${exit_info['price']:.2f}
                    </div>
                    """
            exit_events += '<div style="margin: 4px 0; padding: 4px 8px; background-color: rgba(255,215,0,0.3); border-radius: 4px;"><strong style="color: #b8860b;">🔄 ACTIVE</strong>: Position still open</div>'
        else:
            for exit_info in trade.exits:
                if exit_info['percent'] < 0:
                    # Re-entry
                    exit_events += f"""
                    <div style="margin: 4px 0; padding: 4px 8px; background-color: rgba(0,255,0,0.1); border-radius: 4px;">
                        <strong style="color: green;">+50% RE-ENTRY</strong>: 
                        {exit_info['date'].strftime('%Y-%m-%d')} @ ${exit_info['price']:.2f}
                    </div>
                    """
                else:
                    exit_type = "50%" if "50%" in exit_info['reason'] else "100%" if "100%" in exit_info['reason'] else "SL"
                    exit_color = 'orange' if exit_type == "50%" else 'red' if exit_type == "100%" else 'purple'
                    exit_events += f"""
                    <div style="margin: 4px 0; padding: 4px 8px; background-color: rgba(0,0,0,0.05); border-radius: 4px;">
                        <strong style="color: {exit_color};">{exit_type}</strong>: 
                        {exit_info['date'].strftime('%Y-%m-%d')} @ ${exit_info['price']:.2f}
                    </div>
                    """
        
        # Calculate duration
        if trade.exits:
            final_exit_date = max([e['date'] for e in trade.exits])
            duration_days = (final_exit_date - trade.entry_date).days
        else:
            # Active trade - calculate from entry to today
            from datetime import datetime
            duration_days = (datetime.now() - trade.entry_date).days
        
        # Calculate dollar P&L
        pnl_dollars = trade.calculate_pnl_dollars()
        
        # Format P&L display
        if is_active:
            pnl_percent_display = f"{pnl:+.2f}%"
            pnl_dollar_display = f"${pnl_dollars:+,.2f}"
            unrealized_tag = " <span style='color: #b8860b; font-size: 0.9em;'>(unrealized)</span>"
        else:
            pnl_percent_display = f"{pnl:+.2f}%"
            pnl_dollar_display = f"${pnl_dollars:+,.2f}"
            unrealized_tag = ""
        
        trade_table_html += f"""
                <tr style="background-color: {row_bg};">
                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{i}</td>
                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">{trade.entry_date.strftime('%Y-%m-%d')}</td>
                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">${trade.entry_price:.2f}</td>
                    <td style="padding: 12px; border: 1px solid #ddd;">{exit_events}</td>
                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: {pnl_color};">
                        {pnl_dollar_display}{unrealized_tag}
                    </td>
                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center; font-weight: bold; color: {pnl_color};">
                        {pnl_percent_display}
                    </td>
                    <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">{duration_days} days</td>
                </tr>
        """
    
    trade_table_html += """
            </tbody>
        </table>
    </div>
    """
    
    # ====================================================================
    # SAVE WITH TABLE
    # ====================================================================
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get the chart HTML
    chart_html = fig.to_html(include_plotlyjs='cdn', full_html=False)
    
    # Combine with table
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{symbol} - Complete Strategy View</title>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                font-family: Arial, sans-serif;
            }}
        </style>
    </head>
    <body>
        {chart_html}
        {trade_table_html}
    </body>
    </html>
    """
    
    filename = f'all_panels_{symbol}_{timestamp}.html'
    with open(filename, 'w') as f:
        f.write(full_html)
    print(f"\n✓ Chart saved as {filename}")
    
    with open('index.html', 'w') as f:
        f.write(full_html)
    print(f"✓ Chart saved as index.html (Live)")
    
    fig.show()
    
    return fig


if __name__ == "__main__":
    create_all_panels_chart('AAPL')

