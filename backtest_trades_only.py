"""
Combined Strategy Backtest - TRADES ONLY
=========================================

Clean visualization showing ONLY actual trades taken (no unused signals).

Author: Clean Trade Visualization
"""

import sys
sys.path.append('.')

from backtest_combined_strategy import run_backtest
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


def create_trades_only_chart(symbol='AAPL'):
    """
    Create a clean chart showing only actual trades (no extra signals).
    """
    
    print("\n" + "="*70)
    print("GENERATING TRADES-ONLY CHART")
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
    
    print(f"\nCreating clean trades-only visualization...")
    print(f"✓ {len(trades)} completed trades")
    
    # ====================================================================
    # Create Clean Chart
    # ====================================================================
    
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.05,
        subplot_titles=(
            f'{symbol} Daily Price + Fair Value Bands (100% Exits Only)',
            f'{symbol} Weekly Price + Actual Trades Only',
            f'{symbol} Weekly B-Xtrender',
            f'{symbol} Monthly B-Xtrender',
            'Cumulative P&L (%) - Equity Curve'
        ),
        row_heights=[0.25, 0.25, 0.20, 0.15, 0.15]
    )
    
    # ====================================================================
    # PANEL 1: Daily Price + FVB + 100% Exits Only
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
    
    # Show only 100% exits that actually happened in trades
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
    # PANEL 2: Weekly Price + ACTUAL TRADES ONLY
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
    
    # Show ONLY actual trade entries (not all signals)
    if trades:
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
            row=2, col=1
        )
    
    # Show only actual 50% exits
    exits_50 = []
    for trade in trades:
        for exit_info in trade.exits:
            if exit_info['reason'] == '50% Exit (Weekly 1x)':
                exits_50.append(exit_info)
    
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
            row=2, col=1
        )
    
    # Show only actual stop losses
    stops = []
    for trade in trades:
        for exit_info in trade.exits:
            if exit_info['reason'] == 'Stop Loss (BX Dark Red)':
                stops.append(exit_info)
    
    if stops:
        fig.add_trace(
            go.Scatter(
                x=[s['date'] for s in stops],
                y=[s['price'] for s in stops],
                mode='markers',
                marker=dict(symbol='x', size=12, color='purple', line=dict(width=3)),
                text=[f"STOP LOSS<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}" for s in stops],
                hoverinfo='text',
                name='Stop Loss',
                showlegend=True
            ),
            row=2, col=1
        )
    
    # ====================================================================
    # PANEL 3: Weekly B-Xtrender
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
        row=3, col=1
    )
    
    # Mark ONLY actual trade entries on histogram
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
            row=3, col=1
        )
    
    # ====================================================================
    # PANEL 4: Monthly B-Xtrender
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
        row=4, col=1
    )
    
    # ====================================================================
    # PANEL 5: Equity Curve
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
            row=5, col=1
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=5, col=1)
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'{symbol} - Actual Trades Only (No Extra Signals)<br>'
                 f'<sub>Win Rate: {stats["win_rate"]:.1f}% | Total P&L: +{stats["total_pnl"]:.1f}% | {stats["total_trades"]} Trades</sub>',
            x=0.5,
            xanchor='center'
        ),
        height=1600,
        showlegend=True,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
        xaxis3_rangeslider_visible=False,
        xaxis4_rangeslider_visible=False,
        xaxis5_rangeslider_visible=False
    )
    
    fig.update_yaxes(title_text="Daily Price", row=1, col=1)
    fig.update_yaxes(title_text="Weekly Price", row=2, col=1)
    fig.update_yaxes(title_text="Weekly BX", row=3, col=1)
    fig.update_yaxes(title_text="Monthly BX", row=4, col=1)
    fig.update_yaxes(title_text="P&L (%)", row=5, col=1)
    fig.update_xaxes(title_text="Date", row=5, col=1)
    
    # Save
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'trades_only_{symbol}_{timestamp}.html'
    fig.write_html(filename)
    print(f"\n✓ Clean chart saved as {filename}")
    
    fig.write_html('trades_only.html')
    print(f"✓ Chart saved as trades_only.html")
    
    print(f"\n{'='*70}")
    print("CHART LEGEND:")
    print(f"{'='*70}")
    print("  🟢 Green Stars = Actual trade entries")
    print("  🟠 Orange Stars = 50% exits (Weekly 1x band)")
    print("  🔴 Red Stars = 100% exits (Daily 2x band)")
    print("  🟣 Purple X = Stop losses (Weekly BX dark red)")
    print(f"{'='*70}\n")
    
    fig.show()
    
    return fig, trades, stats


if __name__ == "__main__":
    print("\n" + "="*70)
    print("CLEAN TRADES-ONLY VISUALIZATION")
    print("="*70)
    print("\nShowing ONLY actual trades taken (no unused signals)")
    print("\n" + "="*70 + "\n")
    
    fig, trades, stats = create_trades_only_chart('AAPL')

