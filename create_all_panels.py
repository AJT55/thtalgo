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
            'Cumulative P&L (%)'
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
    for trade in trades:
        for exit_info in trade.exits:
            if exit_info['reason'] == '100% Exit (Daily 2x)':
                exits_100.append(exit_info)
    
    if exits_100:
        fig.add_trace(
            go.Scatter(
                x=[e['date'] for e in exits_100],
                y=[e['price'] for e in exits_100],
                mode='markers',
                marker=dict(symbol='star', size=12, color='red', line=dict(width=2, color='darkred')),
                text=[f"100% EXIT<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for e in exits_100],
                hoverinfo='text',
                name='100% Exit',
                showlegend=True
            ),
            row=1, col=1
        )
        
    # ====================================================================
    # PANEL 2: Weekly Price + Bands Only (Visual Levels)
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
            line=dict(color='rgb(196,177,101)', width=1, dash='dash'),
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
    
    # Trades
    if trades:
        # Entries
        fig.add_trace(
            go.Scatter(
                x=[t.entry_date for t in trades],
                y=[t.entry_price for t in trades],
                mode='markers',
                marker=dict(symbol='star', size=15, color='lime', line=dict(width=2, color='darkgreen')),
                text=[f"ENTRY<br>{t.entry_date.strftime('%Y-%m-%d')}<br>${t.entry_price:.2f}" for t in trades],
                hoverinfo='text',
                name='Entry',
                showlegend=True
            ),
            row=3, col=1
        )
        
        # 50% Exits
        exits_50 = [e for t in trades for e in t.exits if '50%' in e['reason']]
        if exits_50:
            fig.add_trace(
                go.Scatter(
                    x=[e['date'] for e in exits_50],
                    y=[e['price'] for e in exits_50],
                    mode='markers',
                    marker=dict(symbol='star', size=12, color='orange', line=dict(width=2, color='darkorange')),
                    text=[f"50% EXIT<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for e in exits_50],
                    hoverinfo='text',
                    name='50% Exit',
                    showlegend=True
                ),
                row=3, col=1
            )
            
        # Stop Losses
        stops = [e for t in trades for e in t.exits if 'Stop Loss' in e['reason']]
        if stops:
            fig.add_trace(
                go.Scatter(
                    x=[s['date'] for s in stops],
                    y=[s['price'] for s in stops],
                    mode='markers',
                    marker=dict(symbol='x', size=12, color='purple', line=dict(width=3)),
                    text=[f"STOP<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}" for s in stops],
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
    for i in range(len(monthly_bx)):
        bx = monthly_bx['short_term_xtrender'].iloc[i]
        if i == 0:
            color = 'rgba(0,255,0,0.6)' if bx > 0 else 'rgba(255,0,0,0.6)'
        else:
            prev_bx = monthly_bx['short_term_xtrender'].iloc[i-1]
            is_increasing = bx > prev_bx
            if bx > 0:
                color = 'rgba(0,255,0,0.7)' if is_increasing else 'rgba(0,100,0,0.7)'
            else:
                color = 'rgba(255,100,100,0.7)' if is_increasing else 'rgba(139,0,0,0.7)'
        monthly_colors.append(color)
    
    fig.add_trace(
        go.Bar(
            x=monthly_bx.index,
            y=monthly_bx['short_term_xtrender'],
            marker=dict(color=monthly_colors),
            name='Monthly BX',
            showlegend=False
        ),
        row=5, col=1
    )
    
    # ====================================================================
    # PANEL 6: Equity Curve
    # ====================================================================
    
    if trades:
        equity_curve = []
        cumulative_pnl = 0
        equity_dates = []
        
        for trade in trades:
            cumulative_pnl += trade.calculate_pnl()
            equity_curve.append(cumulative_pnl)
            equity_dates.append(trade.exit_date)
        
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
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=6, col=1)
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'{symbol} - ALL-IN-ONE STRATEGY VIEW<br>'
                 f'<sub>Win Rate: {stats["win_rate"]:.1f}% | Total P&L: +{stats["total_pnl"]:.1f}%</sub>',
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
    
    # Save
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'all_panels_{symbol}_{timestamp}.html'
    fig.write_html(filename)
    print(f"\n✓ Chart saved as {filename}")
    
    fig.write_html('index.html')
    print(f"✓ Chart saved as index.html (Live)")
    
    fig.show()
    
    return fig


if __name__ == "__main__":
    create_all_panels_chart('AAPL')

