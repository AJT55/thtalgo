"""
Fair Value Bands Indicator
===========================

Python implementation of the Fair Value Bands indicator from PineScript.
This indicator calculates dynamic support/resistance bands based on fair value
and deviation from price action.

Key Components:
- Fair Value Basis: Smoothed price average (SMA/EMA/etc.)
- Threshold Bands: Based on fair value with adjustable width
- Deviation Bands: 1x and 2x bands based on price spread analysis
- VWAP Support: Volume-weighted average price calculation

Author: Converted from PineScript v6
"""

import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_vwap(df, anchor_period='1D'):
    """
    Calculate VWAP (Volume Weighted Average Price).
    
    Args:
        df: DataFrame with OHLCV data
        anchor_period: Period to reset VWAP calculation
        
    Returns:
        pandas.Series: VWAP values
    """
    if 'Volume' not in df.columns or df['Volume'].isna().all():
        # If no volume data, fall back to simple average
        return df['Close']
    
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    vwap = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    return vwap


def calculate_smoothed_value(source, length, method='SMA', df=None, anchor_period='1D'):
    """
    Calculate smoothed value using various methods.
    
    Args:
        source: Price series to smooth
        length: Smoothing period
        method: Smoothing method (SMA, EMA, HMA, RMA, WMA, VWMA, Median, VWAP)
        df: Full DataFrame (needed for VWMA and VWAP)
        anchor_period: VWAP anchor period
        
    Returns:
        pandas.Series: Smoothed values
    """
    if method == 'SMA':
        return ta.sma(source, length=length)
    elif method == 'EMA':
        return ta.ema(source, length=length)
    elif method == 'HMA':
        return ta.hma(source, length=length)
    elif method == 'RMA':
        return ta.rma(source, length=length)
    elif method == 'WMA':
        return ta.wma(source, length=length)
    elif method == 'VWMA':
        if df is not None and 'Volume' in df.columns:
            return ta.vwma(source, volume=df['Volume'], length=length)
        else:
            return ta.sma(source, length=length)  # Fallback
    elif method == 'Median':
        return source.rolling(window=length).median()
    elif method == 'VWAP':
        if df is not None:
            return calculate_vwap(df, anchor_period)
        else:
            return ta.sma(source, length=length)  # Fallback
    else:
        return ta.wma(source, length=length)  # Default fallback


def get_source(df, source_str):
    """
    Get price source based on string name.
    
    Args:
        df: DataFrame with OHLCV data
        source_str: Source name (OHLC4, Open, High, Low, Close, HL2, HLC3, HLCC4)
        
    Returns:
        pandas.Series: Selected price source
    """
    if source_str == 'Open':
        return df['Open']
    elif source_str == 'High':
        return df['High']
    elif source_str == 'Low':
        return df['Low']
    elif source_str == 'Close':
        return df['Close']
    elif source_str == 'HL2':
        return (df['High'] + df['Low']) / 2
    elif source_str == 'HLC3':
        return (df['High'] + df['Low'] + df['Close']) / 3
    elif source_str == 'HLCC4':
        return (df['High'] + df['Low'] + df['Close'] + df['Close']) / 4
    else:  # Default to OHLC4
        return (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4


def calculate_fair_value_bands(df, 
                               smoothing_type='SMA',
                               length=33,
                               source_str='OHLC4',
                               threshold_up_str='Low',
                               threshold_down_str='High',
                               threshold_boost=1.0,
                               deviation_boost=1.0,
                               vwap_anchor='1D',
                               trend_mode='Cross'):
    """
    Calculate Fair Value Bands indicator.
    
    This indicator creates dynamic support/resistance bands based on:
    1. Fair value (smoothed price average)
    2. Threshold bands (close proximity to fair value)
    3. Deviation bands (1x and 2x standard deviations)
    
    Args:
        df: DataFrame with OHLCV data
        smoothing_type: Type of smoothing (SMA, EMA, HMA, RMA, WMA, VWMA, Median, VWAP)
        length: Smoothing period
        source_str: Price source for fair value calculation
        threshold_up_str: Price source for upper threshold
        threshold_down_str: Price source for lower threshold
        threshold_boost: Multiplier for threshold band width
        deviation_boost: Multiplier for deviation band width
        vwap_anchor: VWAP anchor period (for VWAP smoothing type)
        trend_mode: Trend determination mode (Cross or Direction)
        
    Returns:
        pandas.DataFrame: Original data with added fair value band columns
    """
    result = df.copy()
    
    # Get price sources
    source = get_source(df, source_str)
    threshold_up_src = get_source(df, threshold_up_str)
    threshold_down_src = get_source(df, threshold_down_str)
    
    # Calculate fair value basis
    fair_price_smooth = calculate_smoothed_value(
        source, length, smoothing_type, df, vwap_anchor
    )
    result['fair_value'] = fair_price_smooth
    
    # Calculate spreads (price deviation from fair value)
    low_spread = df['Low'] / fair_price_smooth
    high_spread = df['High'] / fair_price_smooth
    
    # Deviation tracking (when price crosses fair value)
    deviation_down = np.where(
        (df['Low'] < fair_price_smooth) & (df['High'] > fair_price_smooth),
        low_spread,
        np.nan
    )
    deviation_up = np.where(
        (df['Low'] < fair_price_smooth) & (df['High'] > fair_price_smooth),
        high_spread,
        np.nan
    )
    
    # Calculate median deviations (using last 1000 valid values)
    median_up_dev = pd.Series(deviation_up).rolling(window=min(1000, len(df)), min_periods=1).median()
    median_down_dev = pd.Series(deviation_down).rolling(window=min(1000, len(df)), min_periods=1).median()
    
    # Threshold bands
    upper_band = fair_price_smooth * median_up_dev
    lower_band = fair_price_smooth * median_down_dev
    
    band_up_spread = upper_band - fair_price_smooth
    band_down_spread = fair_price_smooth - lower_band
    
    upper_band_boosted = fair_price_smooth + (band_up_spread * threshold_boost)
    lower_band_boosted = fair_price_smooth - (band_down_spread * threshold_boost)
    
    result['threshold_upper'] = upper_band_boosted
    result['threshold_lower'] = lower_band_boosted
    
    # Trend direction calculation
    dir_switch = np.zeros(len(df), dtype=int)
    
    for i in range(1, len(df)):
        if trend_mode == 'Cross':
            trend_rule_up = threshold_up_src.iloc[i] > upper_band_boosted.iloc[i]
            trend_rule_down = threshold_down_src.iloc[i] < lower_band_boosted.iloc[i]
        else:  # Direction
            trend_rule_up = fair_price_smooth.iloc[i] > fair_price_smooth.iloc[i-1]
            trend_rule_down = fair_price_smooth.iloc[i] < fair_price_smooth.iloc[i-1]
        
        if trend_rule_down:
            dir_switch[i] = -1
        elif trend_rule_up:
            dir_switch[i] = 1
        else:
            dir_switch[i] = dir_switch[i-1]  # Maintain previous direction
    
    result['trend_direction'] = dir_switch
    
    # Calculate OHLC4 spread for pivot detection
    ohlc4 = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    ohlc_spread = ohlc4 / fair_price_smooth
    
    # Pivot high/low detection (5 bars left, 5 bars right)
    pivot_ups = []
    pivot_downs = []
    
    for i in range(5, len(df) - 5):
        # Check if this is a pivot high
        if all(ohlc_spread.iloc[i] > ohlc_spread.iloc[i-j] for j in range(1, 6)) and \
           all(ohlc_spread.iloc[i] > ohlc_spread.iloc[i+j] for j in range(1, 6)):
            if df['Low'].iloc[i] > upper_band.iloc[i]:
                pivot_ups.append(ohlc_spread.iloc[i])
        
        # Check if this is a pivot low
        if all(ohlc_spread.iloc[i] < ohlc_spread.iloc[i-j] for j in range(1, 6)) and \
           all(ohlc_spread.iloc[i] < ohlc_spread.iloc[i+j] for j in range(1, 6)):
            if df['High'].iloc[i] < lower_band.iloc[i]:
                pivot_downs.append(ohlc_spread.iloc[i])
    
    # Calculate median pivots (limit to last 2000)
    median_pivot_up = np.median(pivot_ups[-2000:]) if pivot_ups else 1.02
    median_pivot_down = np.median(pivot_downs[-2000:]) if pivot_downs else 0.98
    
    # Deviation bands (1x and 2x)
    pivot_band_up_base = fair_price_smooth * median_pivot_up
    pivot_band_down_base = fair_price_smooth * median_pivot_down
    
    p_band_up_spread = (pivot_band_up_base - fair_price_smooth) * deviation_boost
    p_band_down_spread = (fair_price_smooth - pivot_band_down_base) * deviation_boost
    
    result['deviation_upper_1x'] = fair_price_smooth + p_band_up_spread
    result['deviation_lower_1x'] = fair_price_smooth - p_band_down_spread
    result['deviation_upper_2x'] = result['deviation_upper_1x'] + p_band_up_spread
    result['deviation_lower_2x'] = result['deviation_lower_1x'] - p_band_down_spread
    
    return result


# Default parameters matching PineScript defaults
FAIR_VALUE_PARAMS = {
    'smoothing_type': 'SMA',
    'length': 33,
    'source_str': 'OHLC4',
    'threshold_up_str': 'Low',
    'threshold_down_str': 'High',
    'threshold_boost': 1.0,
    'deviation_boost': 1.0,
    'vwap_anchor': '1D',
    'trend_mode': 'Cross'
}

