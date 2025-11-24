# B-Xtrender Multi-Timeframe Trading Signal Generator

A Python-based trading signal generator that implements the B-Xtrender indicator across multiple timeframes, specifically designed to identify high-probability entry points based on monthly and weekly alignment.

## 📊 What is B-Xtrender?

B-Xtrender is a momentum-based oscillator that combines:
- **RSI (Relative Strength Index)**: Measures momentum strength
- **EMA (Exponential Moving Average)**: Smooths price data
- **T3 Moving Average**: Advanced smoothing technique

The indicator produces values that oscillate around zero, with colors indicating trend strength and direction.

## 🎯 Signal Generation Logic

### Color Coding System

The B-Xtrender uses a 4-color system:

| Color | Condition | Meaning |
|-------|-----------|---------|
| **Light Green** | BX > 0 AND Increasing | Strong bullish momentum |
| **Dark Green** | BX > 0 AND Decreasing | Weakening bullish momentum |
| **Light Red** | BX < 0 AND Increasing | Improving bearish momentum |
| **Dark Red** | BX < 0 AND Decreasing | Strong bearish momentum |

### Entry Signal Criteria

**Conservative Approach (Implemented):**

1. **Monthly Confirmation Required**
   - Wait for monthly bar to close with "light" colors (increasing momentum)
   - Light Green: Positive and gaining strength
   - Light Red: Negative but improving (bottoming signal)

2. **Weekly Entry Triggers**
   - After monthly confirmation, scan for weekly closes with light colors
   - Weekly signals occur in the NEXT month after favorable monthly close
   - Both timeframes must show improving momentum

**Example:**
```
August Monthly: Closes Light Red (improving) → ✅ Confirmation received
September Weeklies: Close Light Green → ⭐ ENTRY SIGNALS generated
```

## 📅 Understanding YFinance Date Alignment

### Critical: Monthly Bar Indexing

**YFinance indexes monthly bars by the first day of the NEXT month:**

```
YFinance Index → Actual Data Period
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2025-07-01     → June 2025 data (Jun 1 - Jun 30)
2025-08-01     → July 2025 data (Jul 1 - Jul 31)
2025-09-01     → August 2025 data (Aug 1 - Aug 31)
2025-10-01     → September 2025 data (Sep 1 - Sep 30)
2025-11-01     → October 2025 data (Oct 1 - Oct 31)
```

### Why This Matters

**The index date represents when the monthly bar CLOSES and becomes final:**
- July 1-31: Data accumulates
- August 1: July bar closes → indexed as `2025-08-01`

**This is standard across financial data providers** - TradingView uses the same system internally.

### Weekly vs Monthly Data Availability

| Timeframe | Update Frequency | Current Data |
|-----------|------------------|--------------|
| **Weekly** | Every 7 days | Shows current/forming week |
| **Monthly** | End of month only | Shows completed months only |

**Example (as of Nov 23, 2025):**
- Weekly: Shows bars through Nov 17, 2025 ✅
- Monthly: Last bar is Oct (index 2025-11-01) ✅
- November monthly: Will appear Dec 1, 2025 ⏳

## 🚀 Installation

### Clone from GitHub

```bash
git clone https://github.com/AJT55/v0-github-project.git
cd v0-github-project
pip install -r requirements.txt
```

**Or download ZIP:**
1. Visit: https://github.com/AJT55/v0-github-project
2. Click "Code" → "Download ZIP"
3. Extract and navigate to folder

### Required Packages

- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `pandas-ta` - Technical analysis indicators
- `yfinance` - Yahoo Finance data download
- `plotly` - Interactive visualizations

## 💻 Usage

### Basic Usage

```python
from bxtrender_panel import create_bxtrender_multi_timeframe

# Generate chart with default settings (AAPL, 5y weekly + 10y monthly)
fig, results, entry_signals = create_bxtrender_multi_timeframe(
    symbol='AAPL',
    save_html=True
)
```

### Custom Periods

```python
# Customize historical data periods
fig, results, entry_signals = create_bxtrender_multi_timeframe(
    symbol='MSFT',
    periods={'weekly': '2y', 'monthly': '5y'},
    save_html=True
)
```

### Command Line

```bash
python bxtrender_panel.py
```

This generates an interactive HTML file: `bxtrender_multitimeframe_with_price_AAPL_YYYYMMDD_HHMMSS.html`

## 📈 Output Visualization

The tool generates a **2x2 grid layout**:

```
┌──────────────────────┬──────────────────────┐
│   Weekly Price       │   Monthly Price      │
│   (Candlesticks)     │   (Candlesticks)     │
│   ⭐ Entry Signals   │                      │
├──────────────────────┼──────────────────────┤
│   Weekly B-Xtrender  │   Monthly B-Xtrender │
│   (Histogram)        │   (Histogram)        │
│   Color-coded bars   │   Color-coded bars   │
└──────────────────────┴──────────────────────┘
```

### Interactive Features

- **Hover tooltips**: Show exact values, dates, and BX calculations
- **Zoom**: Click and drag to zoom into specific periods
- **Pan**: Shift-drag to pan across time
- **Reset**: Double-click to reset view
- **Entry signals**: Gold stars mark entry opportunities

## 📊 Example Signal Flow

```
Timeline: July - October 2025

JULY (2025-08-01 index):
├─ BX Value: -8.25
├─ Previous BX: -14.26
├─ Change: +6.02 ✅ (INCREASING)
├─ Color: Light Red
└─ Result: ✅ CONFIRMATION → Enables August signals

AUGUST Weeklies:
├─ Aug 4: Weekly BX increases → No signal (not light yet)
├─ Aug 11: Weekly BX increases → No signal
├─ Aug 18: Weekly BX increases → No signal
└─ Aug 25: Weekly BX increases → No signal

AUGUST (2025-09-01 index):
├─ BX Value: 0.24
├─ Previous BX: -8.25
├─ Change: +8.49 ✅ (INCREASING)
├─ Color: Light Green
└─ Result: ✅ CONFIRMATION → Enables September signals

SEPTEMBER Weeklies:
├─ Sep 1: Weekly BX = 21.20, Light Green → ⭐ ENTRY SIGNAL
├─ Sep 15: Weekly BX = 22.60, Light Green → ⭐ ENTRY SIGNAL
├─ Sep 22: Weekly BX = 25.43, Light Green → ⭐ ENTRY SIGNAL
└─ Sep 29: Weekly BX = 27.01, Light Green → ⭐ ENTRY SIGNAL
```

## 🔧 Configuration

### Indicator Parameters

Edit `config.py` to customize B-Xtrender calculations:

```python
# Short-term Xtrender (oscillator)
SHORT_L1 = 5   # First EMA period
SHORT_L2 = 20  # Second EMA period
SHORT_L3 = 15  # RSI period

# Long-term Xtrender (trend)
LONG_L1 = 20   # EMA period
LONG_L2 = 15   # RSI period
```

### Data Periods

Modify in `bxtrender_panel.py`:

```python
periods = {
    'weekly': '5y',   # 5 years of weekly data
    'monthly': '10y'  # 10 years of monthly data
}
```

## 📁 Project Structure

```
untitled folder 2/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── config.py                          # Indicator parameters
├── main.py                            # Backtrader integration
├── bxtrender_panel.py                 # Multi-timeframe visualization
├── bxtrender_analysis.ipynb           # Jupyter notebook for analysis
├── data/
│   └── data_handler.py               # YFinance data fetching
├── indicators/
│   └── bxtrender.py                  # B-Xtrender calculation
└── strategies/
    └── bxtrender_strategy.py         # Trading strategy (backtrader)
```

## 🎓 Understanding the Alignment

### Key Concept: "Next Month Entry"

The system uses a **conservative confirmation approach**:

1. **Monthly bar must CLOSE** with favorable momentum
2. **Cannot enter during the same month** (bar is still forming)
3. **Entry signals occur in the NEXT month** after confirmation

### Why This Is Conservative

**Same-Month Entry (Not Used):**
- ❌ Monthly bar still forming
- ❌ Could reverse before month-end
- ❌ Higher risk of false signals

**Next-Month Entry (Implemented):**
- ✅ Monthly confirmation complete
- ✅ Trend has been validated
- ✅ Reduced false signals
- ✅ Lower risk entry

## 📊 Statistics Output

The tool provides comprehensive statistics:

```
Weekly Statistics:
Price Range: $109.60 - $277.05
B-Xtrender Range: -27.92 to 50.00
B-Xtrender Mean: 5.82
B-Xtrender Above zero: 140 bars
B-Xtrender Below zero: 101 bars

Monthly Statistics:
Price Range: $20.28 - $277.05
B-Xtrender Range: -23.00 to 50.00
B-Xtrender Mean: 9.32
B-Xtrender Above zero: 70 bars
B-Xtrender Below zero: 30 bars

Entry Signal Analysis:
Total Entry Signals: 81 (across 5-year period)
```

## 🔄 Data Refresh

### Automatic Updates

- **Weekly data**: Refreshes every time you run the script
- **Monthly data**: Updates when new months close
- **Current month**: Not visible until month-end

### Manual Refresh

```bash
python bxtrender_panel.py
```

Generates a new timestamped HTML file with latest data.

## ⚠️ Important Notes

### Data Source Differences

**YFinance vs TradingView:**
- May have slight OHLC differences
- Updates at different times
- Signals may vary slightly between platforms

**Recommendation**: Use YFinance data consistently for backtesting and signal generation to ensure accuracy.

### Incomplete Monthly Bars

- Current month data appears only AFTER month closes
- November 2025 will appear on December 1, 2025
- This is normal and ensures data integrity

## 🎯 Best Practices for Client Presentation

### 1. Run Fresh Analysis

```bash
# Generate latest chart before presentation
python bxtrender_panel.py
```

### 2. Explain Date Alignment

Use this README section to clarify:
- Why August index contains July data
- Why current month isn't visible yet
- Conservative "next month" entry approach

### 3. Highlight Strengths

- ✅ Multi-timeframe confirmation reduces false signals
- ✅ Conservative approach waits for confirmed trends
- ✅ Interactive visualization allows detailed analysis
- ✅ Historical backtesting shows 81 signals over 5 years

### 4. Show Historical Performance

Point to successful signal examples:
- 2023 recovery signals (Jan-Jun)
- 2024 bull market entries
- Risk management through confirmation

## 📞 Support

For questions or customization requests, refer to the code comments in:
- `bxtrender_panel.py` - Main visualization logic
- `indicators/bxtrender.py` - Indicator calculations
- `data/data_handler.py` - Data fetching

## 📝 License

This project is for professional trading analysis and client presentations.

---

**Last Updated**: November 23, 2025
**Version**: 2.0 (No Date Shifting - Raw YFinance Alignment)
