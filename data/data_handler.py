"""
Data handling utilities for trading strategies
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class DataHandler:
    """
    Handles data fetching and preparation for trading strategies
    """

    def __init__(self):
        self.data_cache = {}

    def fetch_yfinance_data(self, symbol, period='2y', interval='1d', start_date=None, end_date=None):
        """
        Fetch data from Yahoo Finance

        Args:
            symbol: Stock/crypto symbol
            period: Period to fetch (e.g., '1y', '2y', '5y')
            interval: Data interval (e.g., '1d', '1h', '15m')
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with OHLC data
        """
        try:
            # Download data
            if start_date and end_date:
                data = yf.download(symbol, start=start_date, end=end_date, interval=interval)
            else:
                data = yf.download(symbol, period=period, interval=interval)

            # Clean and format data
            if data.empty:
                raise ValueError(f"No data found for symbol {symbol}")

            # Ensure we have the required columns
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in required_cols):
                raise ValueError(f"Missing required columns in data for {symbol}")

            # Remove any rows with NaN values
            data = data.dropna()

            # Cache the data
            cache_key = f"{symbol}_{period}_{interval}_{start_date}_{end_date}"
            self.data_cache[cache_key] = data

            return data

        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None

    def prepare_data(self, data):
        """
        Prepare data for indicator calculations

        Args:
            data: Raw OHLC data

        Returns:
            Prepared DataFrame
        """
        df = data.copy()

        # Handle MultiIndex columns from yfinance
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten MultiIndex columns
            df.columns = df.columns.droplevel(1)

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Sort by date
        df = df.sort_index()

        # Ensure we have numeric data types
        numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Remove any rows with NaN values
        df = df.dropna()

        return df

    def get_data(self, symbol, **params):
        """
        Get and prepare data for a symbol

        Args:
            symbol: Trading symbol
            **params: Data fetching parameters

        Returns:
            Prepared DataFrame
        """
        # Extract data parameters
        period = params.get('period', '2y')
        interval = params.get('interval', '1d')
        start_date = params.get('start_date')
        end_date = params.get('end_date')

        # Fetch data
        raw_data = self.fetch_yfinance_data(symbol, period, interval, start_date, end_date)

        if raw_data is None:
            return None

        # Prepare data
        prepared_data = self.prepare_data(raw_data)

        return prepared_data


def get_sample_data(symbol='AAPL', days=500):
    """
    Get sample data for testing

    Args:
        symbol: Trading symbol
        days: Number of days of data

    Returns:
        DataFrame with sample data
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    handler = DataHandler()
    data = handler.get_data(
        symbol,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        interval='1d'
    )

    return data
