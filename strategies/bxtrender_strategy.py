"""
B-Xtrender Trading Strategy Implementation
"""

import backtrader as bt
from indicators.bxtrender import BXtrender


class BXtrenderIndicator(bt.Indicator):
    """
    Backtrader wrapper for B-Xtrender indicator
    """

    lines = ('short_term_xtrender', 'long_term_xtrender', 'ma_short_term_xtrender',
             'short_buy_signal', 'short_sell_signal')

    params = (
        ('short_l1', 5),
        ('short_l2', 20),
        ('short_l3', 15),
        ('long_l1', 20),
        ('long_l2', 15),
        ('t3_length', 5),
    )

    def __init__(self):
        # Initialize the Python B-Xtrender indicator
        self.bxtrender = BXtrender(
            short_l1=self.params.short_l1,
            short_l2=self.params.short_l2,
            short_l3=self.params.short_l3,
            long_l1=self.params.long_l1,
            long_l2=self.params.long_l2,
            t3_length=self.params.t3_length
        )

        # We'll calculate the indicator in next() method
        self.data_ready = False
        self.calculated_data = None

    def next(self):
        if not self.data_ready:
            # Collect historical data for calculation
            if len(self) >= max(self.params.short_l2, self.params.long_l1, self.params.t3_length) * 2:
                # Create DataFrame from historical data
                import pandas as pd
                closes = [self.data.close[i] for i in range(-len(self.data.close), 0)]
                df = pd.DataFrame({'Close': closes})

                # Calculate B-Xtrender
                self.calculated_data = self.bxtrender.calculate(df)
                self.data_ready = True

        if self.data_ready and len(self.calculated_data) > len(self) - 1:
            # Get current values
            idx = len(self) - 1
            current_data = self.calculated_data.iloc[idx]

            self.lines.short_term_xtrender[0] = current_data['short_term_xtrender']
            self.lines.long_term_xtrender[0] = current_data['long_term_xtrender']
            self.lines.ma_short_term_xtrender[0] = current_data['ma_short_term_xtrender']
            self.lines.short_buy_signal[0] = current_data['short_buy_signal']
            self.lines.short_sell_signal[0] = current_data['short_sell_signal']


class BXtrenderStrategy(bt.Strategy):
    """
    B-Xtrender Trading Strategy
    """

    params = (
        ('short_l1', 5),
        ('short_l2', 20),
        ('short_l3', 15),
        ('long_l1', 20),
        ('long_l2', 15),
        ('t3_length', 5),
        ('stop_loss', 0.02),  # 2% stop loss
        ('take_profit', 0.05),  # 5% take profit
    )

    def __init__(self):
        # Add B-Xtrender indicator
        self.bxtrender = BXtrenderIndicator(
            short_l1=self.params.short_l1,
            short_l2=self.params.short_l2,
            short_l3=self.params.short_l3,
            long_l1=self.params.long_l1,
            long_l2=self.params.long_l2,
            t3_length=self.params.t3_length
        )

        # Track position and signals
        self.position_size = 0
        self.entry_price = 0

        # For logging
        self.order = None

    def next(self):
        # Skip if indicator not ready
        if not self.bxtrender.data_ready:
            return

        # Get current signals
        buy_signal = self.bxtrender.lines.short_buy_signal[0]
        sell_signal = self.bxtrender.lines.short_sell_signal[0]

        # Current position
        current_position = self.position.size

        # Trading logic
        if current_position == 0:  # No position
            if buy_signal > 0:  # Buy signal
                # Calculate position size (simplified - 10% of portfolio)
                size = int((self.broker.getvalue() * 0.1) / self.data.close[0])
                self.order = self.buy(size=size)
                self.entry_price = self.data.close[0]
                self.log(f'BUY EXECUTED: Price={self.data.close[0]:.2f}, Size={size}')

        elif current_position > 0:  # Long position
            # Check stop loss and take profit
            current_price = self.data.close[0]
            pnl_pct = (current_price - self.entry_price) / self.entry_price

            if pnl_pct <= -self.params.stop_loss:  # Stop loss
                self.order = self.sell(size=current_position)
                self.log(f'STOP LOSS: Price={current_price:.2f}, PnL={pnl_pct:.2%}')
            elif pnl_pct >= self.params.take_profit:  # Take profit
                self.order = self.sell(size=current_position)
                self.log(f'TAKE PROFIT: Price={current_price:.2f}, PnL={pnl_pct:.2%}')
            elif sell_signal > 0:  # Sell signal from indicator
                self.order = self.sell(size=current_position)
                self.log(f'SELL SIGNAL: Price={current_price:.2f}, PnL={pnl_pct:.2%}')

    def log(self, txt, dt=None):
        """Logging function"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

    def notify_order(self, order):
        """Order notification"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED: Price={order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED: Price={order.executed.price:.2f}, Cost={order.executed.value:.2f}, Comm={order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Failed')

        self.order = None

    def notify_trade(self, trade):
        """Trade notification"""
        if not trade.isclosed:
            return

        self.log(f'TRADE PROFIT: Gross={trade.pnl:.2f}, Net={trade.pnlcomm:.2f}')


class SimpleBXtrenderStrategy(BXtrenderStrategy):
    """
    Simplified B-Xtrender strategy with basic buy/sell signals
    """

    def next(self):
        # Skip if indicator not ready
        if not self.bxtrender.data_ready:
            return

        # Get current signals
        buy_signal = self.bxtrender.lines.short_buy_signal[0]
        sell_signal = self.bxtrender.lines.short_sell_signal[0]

        # Current position
        current_position = self.position.size

        # Simple logic: Buy on buy signal, sell on sell signal
        if current_position == 0:  # No position
            if buy_signal > 0:  # Buy signal
                size = int((self.broker.getvalue() * 0.1) / self.data.close[0])
                self.order = self.buy(size=size)
                self.log(f'BUY SIGNAL: Price={self.data.close[0]:.2f}, Size={size}')

        elif current_position > 0:  # Long position
            if sell_signal > 0:  # Sell signal
                self.order = self.sell(size=current_position)
                self.log(f'SELL SIGNAL: Price={self.data.close[0]:.2f}')
