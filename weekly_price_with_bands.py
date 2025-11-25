"""
Weekly Price with Fair Value Bands
===================================

Shows weekly price action with Fair Value Bands overlay.
No trade signals - just price and bands.

Author: Weekly FVB Chart
"""

import sys
sys.path.append('.')

import pandas as pd
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

from data.data_handler import DataHandler
from indicators.fair_value_bands import calculate_fair_value_bands, FAIR_VALUE_PARAMS


def create_weekly_bands_chart(symbol='AAPL', period='10y'):
    """
    Create weekly price chart with Fair Value Bands only.
    """
    
    print("\n" + "="*70)
    print(f"WEEKLY PRICE + FAIR VALUE BANDS: {symbol}")
    print("="*70 + "\n")
    
    # Load data
    dh = DataHandler()
    weekly = dh.get_data(symbol, period=period, interval='1wk')
    print(f"✓ Loaded {len(weekly)} weekly bars")
    
    # Calculate Fair Value Bands
    print("Calculating Fair Value Bands...")
    weekly_fvb = calculate_fair_value_bands(weekly, **FAIR_VALUE_PARAMS)
    print("✓ Fair Value Bands calculated")
    
    # Create chart
    print("\nCreating visualization...")
    
    fig = go.Figure()
    
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
        )
    )
    
    # Fair Value
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['fair_value'],
            mode='lines',
            name='Fair Value',
            line=dict(color='blue', width=2),
            showlegend=True
        )
    )
    
    # 1x Upper Band
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_1x'],
            mode='lines',
            name='1x Upper Deviation (50% Exit Target)',
            line=dict(color='rgb(196,177,101)', width=2, dash='dash'),
            showlegend=True
        )
    )
    
    # 2x Upper Band
    fig.add_trace(
        go.Scatter(
            x=weekly_fvb.index,
            y=weekly_fvb['deviation_upper_2x'],
            mode='lines',
            name='2x Upper Deviation',
            line=dict(color='rgb(255,107,107)', width=2, dash='dot'),
            showlegend=True
        )
    )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'{symbol} Weekly Price + Fair Value Bands<br>'
                 f'<sub>Blue=Fair Value | Yellow=1x (50% Exit) | Red=2x Upper</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis_title="Price",
        xaxis_title="Date",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Save
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'weekly_bands_{symbol}_{timestamp}.html'
    fig.write_html(filename)
    print(f"\n✓ Chart saved as {filename}")
    
    fig.write_html('weekly_bands.html')
    print(f"✓ Chart saved as weekly_bands.html")
    
    # Print band values
    print(f"\n{'='*70}")
    print("CURRENT FAIR VALUE BAND LEVELS")
    print(f"{'='*70}")
    print(f"  Current Price: ${weekly_fvb['Close'].iloc[-1]:.2f}")
    print(f"  Fair Value: ${weekly_fvb['fair_value'].iloc[-1]:.2f}")
    print(f"  1x Upper (50% Exit): ${weekly_fvb['deviation_upper_1x'].iloc[-1]:.2f}")
    print(f"  2x Upper: ${weekly_fvb['deviation_upper_2x'].iloc[-1]:.2f}")
    print(f"{'='*70}\n")
    
    fig.show()
    
    return fig


if __name__ == "__main__":
    fig = create_weekly_bands_chart('AAPL', period='10y')

