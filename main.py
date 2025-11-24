"""
Main entry point for B-Xtrender Trading Strategy
"""

import backtrader as bt
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime

from data.data_handler import DataHandler
from strategies.bxtrender_strategy import SimpleBXtrenderStrategy
from config import DATA_PARAMS, STRATEGY_PARAMS, BX_TRENDER_PARAMS


def run_backtest(symbol=None, start_date=None, end_date=None, strategy_params=None):
    """
    Run backtest for B-Xtrender strategy

    Args:
        symbol: Trading symbol (default from config)
        start_date: Start date for backtest
        end_date: End date for backtest
        strategy_params: Strategy parameters

    Returns:
        Backtrader Cerebro instance with results
    """

    # Use defaults from config if not provided
    symbol = symbol or DATA_PARAMS['symbol']
    start_date = start_date or DATA_PARAMS['start_date']
    end_date = end_date or DATA_PARAMS['end_date']
    strategy_params = strategy_params or BX_TRENDER_PARAMS

    # Initialize cerebro
    cerebro = bt.Cerebro()

    # Add strategy
    cerebro.addstrategy(SimpleBXtrenderStrategy, **strategy_params)

    # Get data
    data_handler = DataHandler()
    data = data_handler.get_data(
        symbol,
        start_date=start_date,
        end_date=end_date,
        interval='1d'
    )

    if data is None or data.empty:
        print(f"No data available for {symbol}")
        return None

    print(f"Loaded {len(data)} bars of {symbol} data from {data.index[0]} to {data.index[-1]}")

    # Convert to Backtrader format
    data_feed = bt.feeds.PandasData(dataname=data)

    # Add data to cerebro
    cerebro.adddata(data_feed)

    # Set broker parameters
    cerebro.broker.setcash(STRATEGY_PARAMS['initial_capital'])
    cerebro.broker.setcommission(commission=STRATEGY_PARAMS['commission'])

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

    # Print starting portfolio value
    print(f'Starting Portfolio Value: ${cerebro.broker.getvalue():.2f}')

    # Run backtest
    results = cerebro.run()

    # Print final portfolio value
    final_value = cerebro.broker.getvalue()
    print(f'Final Portfolio Value: ${final_value:.2f}')

    # Print results
    strategy = results[0]

    # Sharpe Ratio
    sharpe = strategy.analyzers.sharpe.get_analysis()
    if sharpe and 'sharperatio' in sharpe and sharpe['sharperatio'] is not None:
        print(f'Sharpe Ratio: {sharpe["sharperatio"]:.3f}')
    else:
        print('Sharpe Ratio: N/A (insufficient data)')

    # Drawdown
    drawdown = strategy.analyzers.drawdown.get_analysis()
    if drawdown and 'max' in drawdown:
        print(f'Max Drawdown: {drawdown["max"]["drawdown"]:.2f}%')
    else:
        print('Max Drawdown: N/A')

    # Returns
    returns = strategy.analyzers.returns.get_analysis()
    if returns and 'rtot' in returns:
        print(f'Total Return: {returns["rtot"]:.2f}%')
    else:
        print('Total Return: N/A')

    # Trade Analysis
    trade_analysis = strategy.analyzers.trades.get_analysis()
    if trade_analysis:
        total_trades = trade_analysis.get('total', {}).get('total', 0)
        won_trades = trade_analysis.get('won', {}).get('total', 0)
        lost_trades = trade_analysis.get('lost', {}).get('total', 0)

        print(f'Total Trades: {total_trades}')
        print(f'Won Trades: {won_trades}')
        print(f'Lost Trades: {lost_trades}')

        if total_trades > 0:
            win_rate = won_trades / total_trades * 100
            print(f'Win Rate: {win_rate:.1f}%')
    else:
        print('No trades executed')

    # Plot results
    try:
        cerebro.plot(style='candlestick', volume=False)
    except Exception as e:
        print(f"Could not create plot: {e}")

    return cerebro, results


def test_indicator_only(symbol='AAPL', days=200):
    """
    Test the B-Xtrender indicator without running a full strategy
    """
    from indicators.bxtrender import calculate_bxtrender
    from data.data_handler import get_sample_data
    import matplotlib.pyplot as plt

    # Get sample data
    data = get_sample_data(symbol, days)
    if data is None:
        print("No data available")
        return

    # Calculate B-Xtrender
    result = calculate_bxtrender(data, **BX_TRENDER_PARAMS)

    # Plot results
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))

    # Price chart
    ax1.plot(result.index, result['Close'], label='Close Price', color='black', alpha=0.7)
    ax1.set_title(f'{symbol} Price with B-Xtrender Signals')
    ax1.legend()

    # Short-term Xtrender
    ax2.plot(result.index, result['short_term_xtrender'], label='Short-term Xtrender', color='blue', alpha=0.7)
    ax2.plot(result.index, result['ma_short_term_xtrender'], label='MA Short-term Xtrender', color='red', linewidth=2)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)

    # Mark buy/sell signals
    buy_signals = result[result['short_buy_signal'] == 1]
    sell_signals = result[result['short_sell_signal'] == 1]

    ax2.scatter(buy_signals.index, buy_signals['ma_short_term_xtrender'],
               marker='^', color='green', s=100, label='Buy Signal')
    ax2.scatter(sell_signals.index, sell_signals['ma_short_term_xtrender'],
               marker='v', color='red', s=100, label='Sell Signal')

    ax2.legend()
    ax2.set_title('Short-term Xtrender Oscillator')

    # Long-term Xtrender
    ax3.plot(result.index, result['long_term_xtrender'], label='Long-term Xtrender', color='purple', alpha=0.7)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    ax3.legend()
    ax3.set_title('Long-term Xtrender Trend')

    plt.tight_layout()
    plt.show()

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'indicator':
        # Test indicator only
        print("Testing B-Xtrender Indicator...")
        test_indicator_only()
    else:
        # Run full backtest
        print("Running B-Xtrender Strategy Backtest...")
        run_backtest()
