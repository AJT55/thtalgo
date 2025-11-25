"""
Clean Trade Visualization - Actual Trades Only
===============================================

Shows ONLY actual trades taken with clear entry/exit markers.
No extra signals, no unused entries - just the 17 trades executed.

Author: Clean Trade Chart
"""

import sys
sys.path.append('.')

from backtest_combined_strategy import run_backtest
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def create_clean_trade_chart(symbol='AAPL'):
    """
    Create a clean chart showing only actual trades without bands.
    """
    
    print("\n" + "="*70)
    print("CLEAN TRADE CHART - ACTUAL TRADES ONLY")
    print("="*70 + "\n")
    
    # Run backtest to get trades
    _, trades, stats = run_backtest(symbol, 'max', '10y', '10y')
    
    # Get data
    from data.data_handler import DataHandler
    from indicators.bxtrender import calculate_bxtrender
    from config import BX_TRENDER_PARAMS
    
    dh = DataHandler()
    weekly = dh.get_data(symbol, period='10y', interval='1wk')
    monthly = dh.get_data(symbol, period='10y', interval='1mo')
    
    weekly_bx = calculate_bxtrender(weekly, **BX_TRENDER_PARAMS)
    monthly_bx = calculate_bxtrender(monthly, **BX_TRENDER_PARAMS)
    
    print(f"\nCreating clean chart for {len(trades)} actual trades...")
    
    # ====================================================================
    # Create Chart - Only Actual Trades
    # ====================================================================
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.06,
        subplot_titles=(
            f'{symbol} Weekly Price - Actual Trades Only ({len(trades)} trades)',
            f'{symbol} Weekly B-Xtrender',
            f'{symbol} Monthly B-Xtrender',
            'Cumulative P&L (%) - Equity Curve'
        ),
        row_heights=[0.35, 0.25, 0.20, 0.20]
    )
    
    # ====================================================================
    # PANEL 1: Weekly Price + ACTUAL TRADES ONLY (NO BANDS)
    # ====================================================================
    
    fig.add_trace(
        go.Candlestick(
            x=weekly.index,
            open=weekly['Open'],
            high=weekly['High'],
            low=weekly['Low'],
            close=weekly['Close'],
            name='Weekly Price',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Show ONLY actual trade entries
    if trades:
        fig.add_trace(
            go.Scatter(
                x=[t.entry_date for t in trades],
                y=[t.entry_price for t in trades],
                mode='markers+text',
                marker=dict(symbol='star', size=20, color='lime', line=dict(width=2, color='darkgreen')),
                text=[f"#{i+1}" for i in range(len(trades))],
                textposition="top center",
                textfont=dict(size=10, color='darkgreen'),
                hovertext=[f"ENTRY #{i+1}<br>{t.entry_date.strftime('%Y-%m-%d')}<br>${t.entry_price:.2f}" for i, t in enumerate(trades)],
                hoverinfo='text',
                name='Entry',
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Show only actual 50% exits
    exits_50 = []
    trade_nums_50 = []
    for i, trade in enumerate(trades):
        for exit_info in trade.exits:
            if exit_info['reason'] == '50% Exit (Weekly 1x)':
                exits_50.append(exit_info)
                trade_nums_50.append(i+1)
    
    if exits_50:
        fig.add_trace(
            go.Scatter(
                x=[e['date'] for e in exits_50],
                y=[e['price'] for e in exits_50],
                mode='markers+text',
                marker=dict(symbol='star', size=16, color='orange', line=dict(width=2, color='darkorange')),
                text=[f"#{n}" for n in trade_nums_50],
                textposition="bottom center",
                textfont=dict(size=10, color='darkorange'),
                hovertext=[f"50% EXIT #{n}<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for n, e in zip(trade_nums_50, exits_50)],
                hoverinfo='text',
                name='50% Exit',
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Show only actual 100% exits
    exits_100 = []
    trade_nums_100 = []
    for i, trade in enumerate(trades):
        for exit_info in trade.exits:
            if exit_info['reason'] == '100% Exit (Daily 2x)':
                exits_100.append(exit_info)
                trade_nums_100.append(i+1)
    
    if exits_100:
        fig.add_trace(
            go.Scatter(
                x=[e['date'] for e in exits_100],
                y=[e['price'] for e in exits_100],
                mode='markers+text',
                marker=dict(symbol='star', size=16, color='red', line=dict(width=2, color='darkred')),
                text=[f"#{n}" for n in trade_nums_100],
                textposition="bottom center",
                textfont=dict(size=10, color='darkred'),
                hovertext=[f"100% EXIT #{n}<br>{e['date'].strftime('%Y-%m-%d')}<br>${e['price']:.2f}" for n, e in zip(trade_nums_100, exits_100)],
                hoverinfo='text',
                name='100% Exit',
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Show only actual stop losses
    stops = []
    trade_nums_stops = []
    for i, trade in enumerate(trades):
        for exit_info in trade.exits:
            if exit_info['reason'] == 'Stop Loss (BX Dark Red)':
                stops.append(exit_info)
                trade_nums_stops.append(i+1)
    
    if stops:
        fig.add_trace(
            go.Scatter(
                x=[s['date'] for s in stops],
                y=[s['price'] for s in stops],
                mode='markers+text',
                marker=dict(symbol='x', size=16, color='purple', line=dict(width=3)),
                text=[f"#{n}" for n in trade_nums_stops],
                textposition="top center",
                textfont=dict(size=10, color='purple'),
                hovertext=[f"STOP #{n}<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}" for n, s in zip(trade_nums_stops, stops)],
                hoverinfo='text',
                name='Stop Loss',
                showlegend=True
            ),
            row=1, col=1
        )
    
    # ====================================================================
    # PANEL 2: Weekly B-Xtrender
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
        row=2, col=1
    )
    
    # Mark ONLY actual trade entries
    if trades:
        entry_bx_vals = []
        for trade in trades:
            idx = weekly_bx.index.get_loc(trade.entry_date)
            entry_bx_vals.append(weekly_bx['short_term_xtrender'].iloc[idx])
        
        fig.add_trace(
            go.Scatter(
                x=[t.entry_date for t in trades],
                y=entry_bx_vals,
                mode='markers+text',
                marker=dict(symbol='star', size=15, color='lime', line=dict(width=2, color='darkgreen')),
                text=[f"#{i+1}" for i in range(len(trades))],
                textposition="top center",
                textfont=dict(size=10, color='darkgreen'),
                showlegend=False
            ),
            row=2, col=1
        )
    
    # ====================================================================
    # PANEL 3: Monthly B-Xtrender
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
        row=3, col=1
    )
    
    # ====================================================================
    # PANEL 4: Equity Curve
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
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(0,255,0,0.1)',
                showlegend=False
            ),
            row=4, col=1
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=4, col=1)
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'{symbol} - ACTUAL TRADES ONLY (No Extra Signals)<br>'
                 f'<sub>Win Rate: {stats["win_rate"]:.1f}% | Total P&L: +{stats["total_pnl"]:.1f}% | {stats["total_trades"]} Trades</sub>',
            x=0.5,
            xanchor='center'
        ),
        height=1400,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        xaxis4_rangeslider_visible=False
    )
    
    fig.update_yaxes(title_text="Weekly Price", row=1, col=1)
    fig.update_yaxes(title_text="Weekly BX", row=2, col=1)
    fig.update_yaxes(title_text="Monthly BX", row=3, col=1)
    fig.update_yaxes(title_text="P&L (%)", row=4, col=1)
    fig.update_xaxes(title_text="Date", row=4, col=1)
    
    # Save
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'clean_trades_{symbol}_{timestamp}.html'
    fig.write_html(filename)
    print(f"\n✓ Clean trades chart saved as {filename}")
    
    fig.write_html('clean_trades.html')
    print(f"✓ Chart saved as clean_trades.html")
    
    # Print trade summary
    print(f"\n{'='*70}")
    print("TRADE SUMMARY")
    print(f"{'='*70}\n")
    
    for i, trade in enumerate(trades, 1):
        summary = trade.get_summary()
        print(f"Trade #{i}:")
        print(f"  Entry: {summary['entry_date'].strftime('%Y-%m-%d')} @ ${summary['entry_price']:.2f}")
        
        for exit_info in summary['exits']:
            exit_type = "50%" if "50%" in exit_info['reason'] else "100%" if "100%" in exit_info['reason'] else "STOP"
            print(f"  Exit:  {exit_info['date'].strftime('%Y-%m-%d')} @ ${exit_info['price']:.2f} ({exit_type})")
        
        pnl_color = "+" if summary['pnl_percent'] > 0 else ""
        print(f"  P&L: {pnl_color}{summary['pnl_percent']:.2f}% | Duration: {summary['duration_days']} days\n")
    
    print(f"{'='*70}\n")
    
    fig.show()
    
    return fig, trades, stats


if __name__ == "__main__":
    fig, trades, stats = create_clean_trade_chart('AAPL')

