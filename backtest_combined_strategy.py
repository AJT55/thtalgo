"""
Combined Strategy Backtest
===========================

Comprehensive backtest of B-Xtrender Entry + Fair Value Bands Exit strategy.

ENTRY CRITERIA:
--------------
1. Monthly B-Xtrender closes light color (increasing)
2. Weekly B-Xtrender closes light color (increasing) in NEXT month
→ ENTER LONG at weekly close

EXIT CRITERIA:
--------------
1. 100% Exit: Daily close > 2x upper FVB → Exit entire position
2. 50% Exit: Weekly close > 1x upper FVB → Exit 50% of position
3. Stop Loss: Weekly BX closes dark red → Exit remaining position

All signals based on CLOSE prices (no lookahead bias).

Author: Combined Strategy Backtester
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


class Trade:
    """Represents a single trade with entry, exits, and P&L tracking."""
    
    def __init__(self, entry_date, entry_price, entry_signal, capital_allocated=10000):
        self.entry_date = entry_date
        self.entry_price = entry_price
        self.entry_signal = entry_signal
        self.capital_allocated = capital_allocated  # Starting capital for this trade
        self.position_size = 1.0  # Start with 100% position
        self.exits = []
        self.exit_date = None
        self.exit_price = None
        self.exit_reason = None
        self.is_closed = False
        
    def add_exit(self, exit_date, exit_price, exit_percent, exit_reason):
        """Record a partial exit, full exit, or re-entry (negative percent)."""
        self.exits.append({
            'date': exit_date,
            'price': exit_price,
            'percent': exit_percent,
            'reason': exit_reason,
            'remaining': max(0, self.position_size - exit_percent) if exit_percent > 0 else self.position_size + abs(exit_percent)
        })
        
        # Update position size (negative = re-entry)
        if exit_percent < 0:
            self.position_size += abs(exit_percent)
        else:
            self.position_size -= exit_percent
        
        if self.position_size <= 0:
            self.is_closed = True
            self.exit_date = exit_date
            self.exit_price = exit_price
            self.exit_reason = exit_reason
    
    def calculate_pnl(self):
        """Calculate total P&L percentage for this trade."""
        if not self.exits:
            return 0
        
        total_pnl_percent = 0
        for exit_info in self.exits:
            pnl_percent = ((exit_info['price'] - self.entry_price) / self.entry_price) * 100
            
            # For re-entries (negative percent), we're buying back at a loss/gain
            if exit_info['percent'] < 0:
                # Re-entry at lower price = missed gains on that 50%
                # Re-entry at higher price = locked in loss on that 50%
                # We account for this by treating it as an exit then re-entry
                weighted_pnl = pnl_percent * abs(exit_info['percent'])
            else:
                # Normal exit
                weighted_pnl = pnl_percent * exit_info['percent']
            
            total_pnl_percent += weighted_pnl
        
        return total_pnl_percent
    
    def calculate_pnl_dollars(self):
        """Calculate total P&L in dollars."""
        pnl_percent = self.calculate_pnl()
        return (pnl_percent / 100) * self.capital_allocated
    
    def get_summary(self):
        """Get trade summary."""
        return {
            'entry_date': self.entry_date,
            'entry_price': self.entry_price,
            'exit_date': self.exit_date,
            'exits': self.exits,
            'pnl_percent': self.calculate_pnl(),
            'is_closed': self.is_closed,
            'duration_days': (self.exit_date - self.entry_date).days if self.exit_date else None
        }


def run_backtest(symbol='AAPL',
                 daily_period='max',
                 weekly_period='10y',
                 monthly_period='10y',
                 starting_capital=10000):
    """
    Run comprehensive backtest of combined strategy.
    
    Returns:
        tuple: (figure, trades, statistics)
    """
    
    print(f"\n{'='*70}")
    print(f"BACKTESTING COMBINED STRATEGY: {symbol}")
    print(f"{'='*70}\n")
    
    # ========================================================================
    # STEP 1: Load and Prepare Data
    # ========================================================================
    print("Loading data...")
    
    data_handler = DataHandler()
    
    daily_data = data_handler.get_data(symbol, period=daily_period, interval='1d')
    print(f"✓ Loaded {len(daily_data)} daily bars")
    
    weekly_data = data_handler.get_data(symbol, period=weekly_period, interval='1wk')
    print(f"✓ Loaded {len(weekly_data)} weekly bars")
    
    monthly_data = data_handler.get_data(symbol, period=monthly_period, interval='1mo')
    print(f"✓ Loaded {len(monthly_data)} monthly bars")
    
    # ========================================================================
    # STEP 2: Calculate All Indicators
    # ========================================================================
    print("\nCalculating indicators...")
    
    weekly_bx = calculate_bxtrender(weekly_data, **BX_TRENDER_PARAMS)
    monthly_bx = calculate_bxtrender(monthly_data, **BX_TRENDER_PARAMS)
    daily_fvb = calculate_fair_value_bands(daily_data, **FAIR_VALUE_PARAMS)
    weekly_fvb = calculate_fair_value_bands(weekly_data, **FAIR_VALUE_PARAMS)
    
    print("✓ All indicators calculated")
    
    # ========================================================================
    # STEP 3: Generate Entry Signals
    # ========================================================================
    print("\nIdentifying entry opportunities...")
    
    entry_signals = []
    
    # Find favorable monthly closes
    for i in range(1, len(monthly_bx)):
        bx_value = monthly_bx['short_term_xtrender'].iloc[i]
        prev_bx = monthly_bx['short_term_xtrender'].iloc[i-1]
        
        if bx_value > prev_bx:  # Light color (increasing)
            monthly_close_date = monthly_bx.index[i]
            
            # Find next monthly close
            if i + 1 < len(monthly_bx):
                next_monthly_date = monthly_bx.index[i + 1]
            else:
                next_monthly_date = weekly_bx.index[-1]
            
            # Find weekly signals in NEXT month (use >= to include first weekly bar)
            weekly_in_range = weekly_bx[
                (weekly_bx.index >= next_monthly_date) & 
                (weekly_bx.index < (monthly_bx.index[i + 2] if i + 2 < len(monthly_bx) else next_monthly_date + pd.DateOffset(months=1)))
            ]
            
            for weekly_date in weekly_in_range.index:
                weekly_idx = weekly_bx.index.get_loc(weekly_date)
                
                if weekly_idx > 0:
                    weekly_bx_value = weekly_bx['short_term_xtrender'].iloc[weekly_idx]
                    prev_weekly_bx = weekly_bx['short_term_xtrender'].iloc[weekly_idx - 1]
                    
                    if weekly_bx_value > prev_weekly_bx:  # Light color
                        entry_signals.append({
                            'date': weekly_date,
                            'price': weekly_bx['Close'].iloc[weekly_idx],
                            'weekly_bx': weekly_bx_value,
                            'monthly_date': monthly_close_date,
                            'monthly_bx': bx_value
                        })
    
    print(f"✓ Found {len(entry_signals)} entry signals")
    
    # ========================================================================
    # STEP 4: Simulate Trades
    # ========================================================================
    print("\nSimulating trades...")
    
    trades = []
    active_trade = None
    
    # Track all potential exit events chronologically
    exit_events = []
    
    # Daily 100% exits
    for date in daily_fvb.index:
        if daily_fvb.loc[date, 'Close'] > daily_fvb.loc[date, 'deviation_upper_2x']:
            exit_events.append({
                'date': date,
                'price': daily_fvb.loc[date, 'Close'],
                'type': '100_exit',
                'band': daily_fvb.loc[date, 'deviation_upper_2x']
            })
    
    # Weekly 50% exits
    for date in weekly_fvb.index:
        if weekly_fvb.loc[date, 'Close'] > weekly_fvb.loc[date, 'deviation_upper_1x']:
            exit_events.append({
                'date': date,
                'price': weekly_fvb.loc[date, 'Close'],
                'type': '50_exit',
                'band': weekly_fvb.loc[date, 'deviation_upper_1x']
            })
    
    # Weekly 50% re-entries (price closes below fair value after taking profit)
    for date in weekly_fvb.index:
        if weekly_fvb.loc[date, 'Close'] < weekly_fvb.loc[date, 'fair_value']:
            exit_events.append({
                'date': date,
                'price': weekly_fvb.loc[date, 'Close'],
                'type': '50_reentry',
                'fair_value': weekly_fvb.loc[date, 'fair_value']
            })
    
    # Weekly BX stop losses
    for i in range(1, len(weekly_bx)):
        bx = weekly_bx['short_term_xtrender'].iloc[i]
        prev_bx = weekly_bx['short_term_xtrender'].iloc[i-1]
        
        if bx < 0 and bx < prev_bx:  # Dark red
            exit_events.append({
                'date': weekly_bx.index[i],
                'price': weekly_bx['Close'].iloc[i],
                'type': 'stop_loss',
                'bx': bx
            })
    
    # Sort all events chronologically
    all_events = sorted(entry_signals + exit_events, key=lambda x: x['date'])
    
    # Process events sequentially
    for event in all_events:
        if 'weekly_bx' in event:  # This is an entry signal
            # Only enter if NO active trade OR previous trade is fully closed
            if active_trade is None or active_trade.is_closed:
                # Open new trade (only one position at a time)
                active_trade = Trade(
                    entry_date=event['date'],
                    entry_price=event['price'],
                    entry_signal=event,
                    capital_allocated=starting_capital
                )
                trades.append(active_trade)
            # else: Skip this entry signal - already in a trade
        
        elif active_trade and not active_trade.is_closed:  # This is an exit signal
            # Only process exits after entry
            if event['date'] > active_trade.entry_date:
                
                if event['type'] == '50_exit' and active_trade.position_size > 0.5:
                    # 50% exit
                    active_trade.add_exit(
                        exit_date=event['date'],
                        exit_price=event['price'],
                        exit_percent=0.5,
                        exit_reason='50% Exit (Weekly 1x)'
                    )
                
                elif event['type'] == '100_exit' and active_trade.position_size > 0:
                    # 100% exit of remaining position
                    active_trade.add_exit(
                        exit_date=event['date'],
                        exit_price=event['price'],
                        exit_percent=active_trade.position_size,
                        exit_reason='100% Exit (Daily 2x)'
                    )
                
                elif event['type'] == '50_reentry' and active_trade.position_size == 0.5:
                    # Re-enter 50% after pullback below fair value
                    active_trade.add_exit(
                        exit_date=event['date'],
                        exit_price=event['price'],
                        exit_percent=-0.5,  # Negative = adding back position
                        exit_reason='50% Re-Entry (Below Fair Value)'
                    )
                
                elif event['type'] == 'stop_loss' and active_trade.position_size > 0:
                    # Stop loss - exit remaining position
                    active_trade.add_exit(
                        exit_date=event['date'],
                        exit_price=event['price'],
                        exit_percent=active_trade.position_size,
                        exit_reason='Stop Loss (BX Dark Red)'
                    )
    
    # Separate completed and active trades
    completed_trades = [t for t in trades if t.is_closed]
    active_trades = [t for t in trades if not t.is_closed]
    
    print(f"✓ Simulated {len(completed_trades)} completed trades")
    if active_trades:
        print(f"✓ Found {len(active_trades)} active (incomplete) trade(s)")
    
    # ========================================================================
    # STEP 5: Calculate Statistics
    # ========================================================================
    print("\nCalculating performance metrics...")
    
    if completed_trades:
        pnls = [t.calculate_pnl() for t in completed_trades]
        pnls_dollars = [t.calculate_pnl_dollars() for t in completed_trades]
        durations = [t.get_summary()['duration_days'] for t in completed_trades]
        
        winning_trades = [p for p in pnls if p > 0]
        losing_trades = [p for p in pnls if p < 0]
        winning_dollars = [d for d in pnls_dollars if d > 0]
        losing_dollars = [d for d in pnls_dollars if d < 0]
        
        statistics = {
            'total_trades': len(completed_trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(completed_trades) * 100,
            'avg_win': np.mean(winning_trades) if winning_trades else 0,
            'avg_loss': np.mean(losing_trades) if losing_trades else 0,
            'avg_pnl': np.mean(pnls),
            'total_pnl': np.sum(pnls),
            'total_pnl_dollars': np.sum(pnls_dollars),
            'final_capital': starting_capital + np.sum(pnls_dollars),
            'max_win': max(pnls) if pnls else 0,
            'max_loss': min(pnls) if pnls else 0,
            'avg_duration': np.mean(durations) if durations else 0,
            'profit_factor': abs(sum(winning_trades) / sum(losing_trades)) if losing_trades and sum(losing_trades) != 0 else float('inf'),
            'starting_capital': starting_capital
        }
    else:
        statistics = {}
    
    # ========================================================================
    # STEP 6: Create Visualization
    # ========================================================================
    print("\nCreating backtest visualization...")
    
    fig = make_subplots(
        rows=5, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.05,
        subplot_titles=(
            f'{symbol} Daily Price + Fair Value Bands (100% Exits)',
            f'{symbol} Weekly Price - Entry & Exit Signals',
            f'{symbol} Weekly B-Xtrender - Entry Confirmation',
            f'{symbol} Monthly B-Xtrender - Entry Confirmation',
            'Cumulative P&L (%) - Equity Curve'
        ),
        row_heights=[0.25, 0.25, 0.20, 0.15, 0.15]
    )
    
    # ====================================================================
    # PANEL 1: Daily Price with Fair Value Bands
    # ====================================================================
    
    # Trim daily to last 10 years for display
    ten_years_ago = daily_fvb.index[-1] - pd.DateOffset(years=10)
    daily_display = daily_fvb[daily_fvb.index >= ten_years_ago]
    
    # Candlesticks
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
    
    # ====================================================================
    # PANEL 2: Weekly Price with Entry/Exit Signals
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
    
    # 1x Upper Band
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_1x'],
            mode='lines',
            name='1x Upper (50% Exit)',
            line=dict(color='rgb(196,177,101)', width=1.5, dash='dash'),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 2x Upper Band
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_2x'],
            mode='lines',
            name='2x Upper',
            line=dict(color='rgb(255,107,107)', width=1.5, dash='dot'),
            showlegend=False
        ),
        row=2, col=1
    )
    
    # Entry signals
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
                text=[f"ENTRY<br>{s['date'].strftime('%Y-%m-%d')}<br>${s['price']:.2f}<br>W_BX:{s['weekly_bx']:.1f}" 
                      for s in entry_signals],
                hoverinfo='text',
                name='Entry',
                showlegend=True
            ),
            row=2, col=1
        )
    
    # Exit signals on weekly chart
    for trade in completed_trades:
        for exit_info in trade.exits:
            if exit_info['reason'] == '50% Exit (Weekly 1x)':
                color = 'orange'
                symbol_shape = 'star'
            elif exit_info['reason'] == '100% Exit (Daily 2x)':
                color = 'red'
                symbol_shape = 'star'
            else:  # Stop loss
                color = 'purple'
                symbol_shape = 'x'
            
            fig.add_trace(
                go.Scatter(
                    x=[exit_info['date']],
                    y=[exit_info['price']],
                    mode='markers',
                    marker=dict(
                        symbol=symbol_shape,
                        size=12,
                        color=color,
                        line=dict(width=2)
                    ),
                    text=f"{exit_info['reason']}<br>{exit_info['date'].strftime('%Y-%m-%d')}<br>${exit_info['price']:.2f}",
                    hoverinfo='text',
                    showlegend=False
                ),
                row=2, col=1
            )
    
    # ====================================================================
    # PANEL 3: Weekly B-Xtrender Histogram
    # ====================================================================
    
    # Color-coded bars
    weekly_colors = []
    for i in range(len(weekly_bx)):
        bx = weekly_bx['short_term_xtrender'].iloc[i]
        
        if i == 0:
            color = 'rgba(0,255,0,0.6)' if bx > 0 else 'rgba(255,0,0,0.6)'
        else:
            prev_bx = weekly_bx['short_term_xtrender'].iloc[i-1]
            is_increasing = bx > prev_bx
            
            if bx > 0:
                color = 'rgba(0,255,0,0.7)' if is_increasing else 'rgba(0,100,0,0.7)'  # Light/dark green
            else:
                color = 'rgba(255,100,100,0.7)' if is_increasing else 'rgba(139,0,0,0.7)'  # Light/dark red
        
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
    
    # Mark entry signals on histogram
    if entry_signals:
        entry_bx_vals = []
        for signal in entry_signals:
            idx = weekly_bx.index.get_loc(signal['date'])
            entry_bx_vals.append(weekly_bx['short_term_xtrender'].iloc[idx])
        
        fig.add_trace(
            go.Scatter(
                x=[s['date'] for s in entry_signals],
                y=entry_bx_vals,
                mode='markers',
                marker=dict(symbol='star', size=12, color='lime', line=dict(width=2, color='darkgreen')),
                showlegend=False
            ),
            row=3, col=1
        )
    
    # ====================================================================
    # PANEL 4: Monthly B-Xtrender Histogram
    # ====================================================================
    
    # Color-coded bars
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
    # PANEL 5: Equity Curve (Cumulative P&L)
    # ====================================================================
    
    if completed_trades:
        # Calculate cumulative P&L
        equity_curve = []
        cumulative_pnl = 0
        equity_dates = []
        
        for trade in completed_trades:
            cumulative_pnl += trade.calculate_pnl()
            equity_curve.append(cumulative_pnl)
            equity_dates.append(trade.exit_date)
        
        fig.add_trace(
            go.Scatter(
                x=equity_dates,
                y=equity_curve,
                mode='lines+markers',
                name='Equity Curve',
                line=dict(color='green', width=2),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(0,255,0,0.1)',
                showlegend=False
            ),
            row=5, col=1
        )
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=5, col=1)
    
    # ====================================================================
    # Layout
    # ====================================================================
    
    fig.update_layout(
        title=dict(
            text=f'{symbol} - Combined Strategy Backtest<br>'
                 f'<sub>Green=Entry | Orange=50% Exit | Red=100% Exit | Purple=Stop Loss</sub>',
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
        xaxis4_rangeslider_visible=False
    )
    
    fig.update_yaxes(title_text="Daily Price", row=1, col=1)
    fig.update_yaxes(title_text="Weekly Price", row=2, col=1)
    fig.update_yaxes(title_text="Weekly BX", row=3, col=1)
    fig.update_yaxes(title_text="Monthly BX", row=4, col=1)
    fig.update_yaxes(title_text="Cumulative P&L (%)", row=5, col=1)
    fig.update_xaxes(title_text="Date", row=5, col=1)
    
    # Save
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'backtest_{symbol}_{timestamp}.html'
    fig.write_html(filename)
    print(f"\n✓ Backtest chart saved as {filename}")
    
    fig.write_html('index.html')
    print(f"✓ Chart saved as index.html")
    
    # ========================================================================
    # STEP 7: Print Detailed Results
    # ========================================================================
    print(f"\n{'='*70}")
    print("BACKTEST RESULTS")
    print(f"{'='*70}\n")
    
    if statistics:
        print(f"📊 PERFORMANCE SUMMARY:")
        print("-" * 70)
        print(f"  Starting Capital: ${statistics['starting_capital']:,.2f}")
        print(f"  Final Capital: ${statistics['final_capital']:,.2f}")
        print(f"  Total P&L: ${statistics['total_pnl_dollars']:+,.2f} ({statistics['total_pnl']:+.2f}%)")
        print(f"  Total Trades: {statistics['total_trades']}")
        print(f"  Winning Trades: {statistics['winning_trades']}")
        print(f"  Losing Trades: {statistics['losing_trades']}")
        print(f"  Win Rate: {statistics['win_rate']:.1f}%")
        print(f"  Average Win: {statistics['avg_win']:.2f}%")
        print(f"  Average Loss: {statistics['avg_loss']:.2f}%")
        print(f"  Average P&L: {statistics['avg_pnl']:.2f}%")
        print(f"  Max Win: {statistics['max_win']:.2f}%")
        print(f"  Max Loss: {statistics['max_loss']:.2f}%")
        print(f"  Profit Factor: {statistics['profit_factor']:.2f}")
        print(f"  Avg Duration: {statistics['avg_duration']:.0f} days")
        
        print(f"\n📋 TRADE LOG (Last 10 Trades):")
        print("-" * 70)
        
        for trade in completed_trades[-10:]:
            summary = trade.get_summary()
            print(f"\n  Entry: {summary['entry_date'].strftime('%Y-%m-%d')} @ ${summary['entry_price']:.2f}")
            
            for exit_info in summary['exits']:
                print(f"    Exit: {exit_info['date'].strftime('%Y-%m-%d')} @ ${exit_info['price']:.2f} "
                      f"({exit_info['percent']*100:.0f}%) - {exit_info['reason']}")
            
            print(f"  P&L: {summary['pnl_percent']:+.2f}% | Duration: {summary['duration_days']} days")
    else:
        print("No completed trades found in backtest period.")
    
    print(f"\n{'='*70}\n")
    
    fig.show()
    
    # Return ALL trades (completed + active) for visualization
    return fig, trades, statistics


if __name__ == "__main__":
    print("\n" + "="*70)
    print("COMBINED STRATEGY BACKTEST")
    print("="*70)
    print("\nStrategy Rules:")
    print("  ENTRY: Monthly + Weekly B-Xtrender light colors")
    print("  EXIT:  Daily 2x FVB (100%) OR Weekly 1x FVB (50%)")
    print("  STOP:  Weekly B-Xtrender dark red")
    print("\n" + "="*70 + "\n")
    
    fig, trades, stats = run_backtest(
        symbol='AAPL',
        daily_period='max',
        weekly_period='10y',
        monthly_period='10y'
    )

