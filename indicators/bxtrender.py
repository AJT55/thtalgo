"""
B-Xtrender Indicator Implementation
Converted from PineScript to Python
"""

import pandas as pd
import numpy as np
import pandas_ta as ta


class BXtrender:
    """
    B-Xtrender Oscillator indicator implementation
    """

    def __init__(self, short_l1=5, short_l2=20, short_l3=15, long_l1=20, long_l2=15, t3_length=5):
        """
        Initialize B-Xtrender indicator

        Args:
            short_l1: Short-term EMA length 1 (default: 5)
            short_l2: Short-term EMA length 2 (default: 20)
            short_l3: Short-term RSI length (default: 15)
            long_l1: Long-term EMA length 1 (default: 20)
            long_l2: Long-term RSI length (default: 15)
            t3_length: T3 moving average length (default: 5)
        """
        self.short_l1 = short_l1
        self.short_l2 = short_l2
        self.short_l3 = short_l3
        self.long_l1 = long_l1
        self.long_l2 = long_l2
        self.t3_length = t3_length

    def t3(self, src, length):
        """
        T3 moving average implementation

        Args:
            src: Source series
            length: Period length

        Returns:
            T3 moving average series
        """
        # Calculate multiple EMAs
        xe1 = ta.ema(src, length=length)
        xe2 = ta.ema(xe1, length=length)
        xe3 = ta.ema(xe2, length=length)
        xe4 = ta.ema(xe3, length=length)
        xe5 = ta.ema(xe4, length=length)
        xe6 = ta.ema(xe5, length=length)

        # T3 coefficients
        b = 0.7
        c1 = -b * b * b
        c2 = 3 * b * b + 3 * b * b * b
        c3 = -6 * b * b - 3 * b - 3 * b * b * b
        c4 = 1 + 3 * b + b * b * b + 3 * b * b

        # Calculate T3 average
        t3_avg = c1 * xe6 + c2 * xe5 + c3 * xe4 + c4 * xe3

        return t3_avg

    def calculate(self, data):
        """
        Calculate B-Xtrender indicator

        Args:
            data: DataFrame with OHLC data

        Returns:
            DataFrame with B-Xtrender calculations
        """
        df = data.copy()

        # Calculate EMAs for short-term Xtrender
        ema_short_l1 = ta.ema(df['Close'], length=self.short_l1)
        ema_short_l2 = ta.ema(df['Close'], length=self.short_l2)

        # Calculate short-term Xtrender: RSI(EMA(close, short_l1) - EMA(close, short_l2), short_l3) - 50
        short_diff = ema_short_l1 - ema_short_l2
        short_term_xtrender = ta.rsi(short_diff, length=self.short_l3) - 50

        # Calculate long-term Xtrender: RSI(EMA(close, long_l1), long_l2) - 50
        ema_long_l1 = ta.ema(df['Close'], length=self.long_l1)
        long_term_xtrender = ta.rsi(ema_long_l1, length=self.long_l2) - 50

        # Calculate T3 moving average of short-term Xtrender
        ma_short_term_xtrender = self.t3(short_term_xtrender, self.t3_length)

        # Calculate signals
        short_xtrender_signal = (short_term_xtrender > 0).astype(int) * 2 - 1  # 1 for positive, -1 for negative
        short_xtrender_trend = (short_term_xtrender > short_term_xtrender.shift(1)).astype(int)

        long_xtrender_signal = (long_term_xtrender > 0).astype(int) * 2 - 1  # 1 for positive, -1 for negative
        long_xtrender_trend = (long_term_xtrender > long_term_xtrender.shift(1)).astype(int)

        ma_short_trend = (ma_short_term_xtrender > ma_short_term_xtrender.shift(1)).astype(int)

        # Buy/Sell signals based on trend changes
        short_buy_signal = (ma_short_term_xtrender > ma_short_term_xtrender.shift(1)) & \
                          (ma_short_term_xtrender.shift(1) < ma_short_term_xtrender.shift(2))
        short_sell_signal = (ma_short_term_xtrender < ma_short_term_xtrender.shift(1)) & \
                           (ma_short_term_xtrender.shift(1) > ma_short_term_xtrender.shift(2))

        # Add results to dataframe
        df['short_term_xtrender'] = short_term_xtrender
        df['long_term_xtrender'] = long_term_xtrender
        df['ma_short_term_xtrender'] = ma_short_term_xtrender

        df['short_xtrender_signal'] = short_xtrender_signal
        df['short_xtrender_trend'] = short_xtrender_trend
        df['long_xtrender_signal'] = long_xtrender_signal
        df['long_xtrender_trend'] = long_xtrender_trend
        df['ma_short_trend'] = ma_short_trend

        df['short_buy_signal'] = short_buy_signal.astype(int)
        df['short_sell_signal'] = short_sell_signal.astype(int)

        return df


def calculate_bxtrender(data, **params):
    """
    Convenience function to calculate B-Xtrender indicator

    Args:
        data: DataFrame with OHLC data
        **params: B-Xtrender parameters

    Returns:
        DataFrame with B-Xtrender calculations
    """
    indicator = BXtrender(**params)
    return indicator.calculate(data)
