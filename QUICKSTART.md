# 🚀 Quick Start Guide - B-Xtrender Trading System

## For Mac Users

### Step 1: Clone from GitHub

**Download the project from GitHub:**

```bash
cd ~/Desktop
git clone https://github.com/AJT55/algo.git
cd algo
```

**Or download as ZIP:**
1. Go to: https://github.com/AJT55/algo
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract to your Desktop

---

### Step 2: Open Terminal

**Two ways to open Terminal on Mac:**

**Option A:** Spotlight Search
1. Press `Cmd + Space`
2. Type "Terminal"
3. Press Enter

**Option B:** Finder
1. Open Finder
2. Go to Applications → Utilities → Terminal
3. Double-click Terminal

---

### Step 3: Install Python (If Not Already Installed)

**Check if Python is installed:**

```bash
python3 --version
```

**If you see something like `Python 3.x.x`, you're good! Skip to Step 4.**

**If not installed, install Python:**

1. Go to: https://www.python.org/downloads/
2. Download Python 3.11 or newer for macOS
3. Run the installer
4. Follow the installation wizard
5. Verify installation: `python3 --version`

---

### Step 4: Navigate to Project Folder

In Terminal, type:

```bash
cd ~/Desktop/algo
```

**Or if you cloned/extracted it elsewhere:**

```bash
cd /path/to/where/you/cloned/algo
```

**Tip:** You can drag the folder from Finder into Terminal to auto-fill the path!

---

### Step 5: Install Required Packages

Copy and paste this command:

```bash
pip3 install -r requirements.txt
```

**This will install:**
- pandas (data manipulation)
- numpy (numerical operations)
- pandas-ta (technical indicators)
- yfinance (market data)
- plotly (interactive charts)
- matplotlib (plotting)
- backtrader (backtesting)

**Wait for installation to complete** (usually 1-2 minutes)

---

### Step 6: Run the Analyzer

**Simply type:**

```bash
python3 bxtrender_panel.py
```

**What happens:**
1. Script downloads latest market data
2. Calculates B-Xtrender for weekly & monthly
3. Identifies entry signals
4. Generates interactive HTML chart
5. Saves to: `bxtrender_multitimeframe_with_price_AAPL_YYYYMMDD_HHMMSS.html`

**Expected output:**

```
Loading multi-timeframe data for AAPL...
Loading weekly data (5y)...
Loaded 261 weekly data points
Calculating B-Xtrender indicator...
Loading monthly data (10y)...
Loaded 120 monthly data points
Calculating B-Xtrender indicator...
Creating multi-timeframe B-Xtrender visualization with price action...
Found 63 entry signals in months following favorable monthly closes
Multi-timeframe chart with price action saved as bxtrender_multitimeframe_with_price_AAPL_20251123_170000.html

Weekly Statistics:
Price Range: $109.60 - $277.05
B-Xtrender Range: -27.92 to 50.00
...
```

---

### Step 7: View the Results

**The HTML file is now in the project folder!**

**To open it:**

**Option A:** Double-click the HTML file in Finder

**Option B:** From Terminal:
```bash
open bxtrender_multitimeframe_with_price_AAPL_*.html
```

**The chart will open in your default web browser** (Chrome, Safari, Firefox, etc.)

---

## 🎯 Quick Reference Commands

### Run Analysis (Default: AAPL, 5y weekly, 10y monthly)
```bash
python3 bxtrender_panel.py
```

### Analyze Different Symbol
```bash
# Edit line 656 in bxtrender_panel.py
# Change symbol='AAPL' to symbol='MSFT' (or any symbol)
# Then run: python3 bxtrender_panel.py
```

### Re-run Analysis (Fresh Data)
```bash
python3 bxtrender_panel.py
```
*Generates new timestamped HTML file each time*

### View All Generated Charts
```bash
ls -lt *.html
```

### Clean Up Old Charts (Keep Only Latest)
```bash
ls -t *.html | tail -n +2 | xargs rm -f
```

---

## 📁 Project Files Overview

```
untitled folder 2/
├── QUICKSTART.md                 ← You are here!
├── README.md                     ← Technical documentation
├── USER_GUIDE.md                 ← Detailed user manual
├── CLIENT_PRESENTATION.md        ← Business presentation
│
├── requirements.txt              ← Python dependencies
├── config.py                     ← Customizable parameters
│
├── bxtrender_panel.py            ← Main script (run this!)
├── main.py                       ← Backtrader integration
├── bxtrender_analysis.ipynb      ← Jupyter notebook
│
├── data/
│   └── data_handler.py          ← YFinance data fetching
│
├── indicators/
│   └── bxtrender.py             ← B-Xtrender calculation
│
└── strategies/
    └── bxtrender_strategy.py    ← Trading strategy
```

---

## ⚙️ Customization (Optional)

### Change Symbol

**Edit:** `bxtrender_panel.py`  
**Line:** 656 (bottom of file)

```python
# Change AAPL to any symbol
fig, results, entry_signals = create_bxtrender_multi_timeframe(
    symbol='MSFT',  # ← Change this
    save_html=True
)
```

### Change Data Periods

```python
periods = {
    'weekly': '2y',   # 2 years instead of 5
    'monthly': '5y'   # 5 years instead of 10
}

fig, results, entry_signals = create_bxtrender_multi_timeframe(
    symbol='AAPL',
    periods=periods,  # ← Add this
    save_html=True
)
```

### Adjust Indicator Sensitivity

**Edit:** `config.py`

```python
BX_TRENDER_PARAMS = {
    'short_l1': 3,   # More sensitive (was 5)
    'short_l2': 15,  # More sensitive (was 20)
    'short_l3': 10,  # More sensitive (was 15)
    ...
}
```

---

## 🔧 Troubleshooting

### "Command not found: python3"

**Solution:**
- Try `python` instead of `python3`
- Or install Python from python.org

### "Command not found: pip3"

**Solution:**
- Try `pip` instead of `pip3`
- Or install pip: `python3 -m ensurepip --upgrade`

### "Permission denied"

**Solution:**
```bash
chmod +x bxtrender_panel.py
python3 bxtrender_panel.py
```

### "No module named 'pandas'" (after pip install)

**Solution:**
```bash
pip3 install --user -r requirements.txt
```

### Chart doesn't open in browser

**Solution:**
1. Find the HTML file in Finder
2. Right-click → Open With → Chrome (or your browser)

### "No data available for any timeframe"

**Solution:**
- Check internet connection
- Try shorter period: `periods={'weekly': '1y', 'monthly': '2y'}`

---

## 📊 Understanding the Output

### The Chart Shows:

```
┌─────────────────────────┬─────────────────────────┐
│  WEEKLY PRICE           │  MONTHLY PRICE          │
│  • Candlesticks         │  • Candlesticks         │
│  • Gold stars (⭐) =    │  • Long-term view       │
│    Entry signals        │                         │
├─────────────────────────┼─────────────────────────┤
│  WEEKLY B-XTRENDER      │  MONTHLY B-XTRENDER     │
│  • Color bars           │  • Color bars           │
│  • Green = Bullish      │  • Red = Bearish        │
│  • Light = Improving    │  • Dark = Worsening     │
└─────────────────────────┴─────────────────────────┘
```

### Colors Explained:

- 🟢 **Light Green**: Strong bullish momentum (best)
- 🟢 **Dark Green**: Bullish but weakening
- 🔴 **Light Red**: Bearish but improving (bottoming)
- 🔴 **Dark Red**: Strong bearish momentum (worst)

### Entry Signals (⭐):

**What they mean:**
- Monthly confirmed improvement
- Weekly showing light colors
- High-probability entry point

**Hover over stars** to see:
- Entry date
- Entry price
- Which month confirmed the signal

---

## 📱 Next Steps

### 1. Run Your First Analysis (5 minutes)
```bash
cd ~/Desktop/algo
pip3 install -r requirements.txt
python3 bxtrender_panel.py
open bxtrender_*.html
```

### 2. Read the Documentation (30 minutes)
- `USER_GUIDE.md` - How to use the tool
- `CLIENT_PRESENTATION.md` - Understanding the system
- `README.md` - Technical details

### 3. Customize for Your Needs (15 minutes)
- Edit `config.py` for different parameters
- Modify `bxtrender_panel.py` for different symbols
- Experiment with different timeframes

### 4. Integrate into Your Workflow
- Run weekly on Monday mornings
- Track signals in a spreadsheet
- Combine with other analysis

---

## 💡 Pro Tips

### Tip 1: Analyze Multiple Symbols

Create a file `analyze_batch.py`:

```python
from bxtrender_panel import create_bxtrender_multi_timeframe

symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']

for symbol in symbols:
    print(f"\n{'='*50}")
    print(f"Analyzing {symbol}...")
    print('='*50)
    
    fig, results, signals = create_bxtrender_multi_timeframe(
        symbol=symbol,
        save_html=True
    )
    
    print(f"{symbol}: {len(signals)} signals found")
```

Run: `python3 analyze_batch.py`

### Tip 2: Weekly Automation (macOS)

Create a weekly cron job:

```bash
# Open cron editor
crontab -e

# Add this line (runs every Monday at 9 AM):
0 9 * * 1 cd ~/Desktop/algo && python3 bxtrender_panel.py
```

### Tip 3: Export Signal Data

```python
import pandas as pd
from bxtrender_panel import create_bxtrender_multi_timeframe

fig, results, signals = create_bxtrender_multi_timeframe('AAPL')

# Save signals to CSV
df = pd.DataFrame(signals)
df.to_csv('aapl_signals.csv', index=False)
print(f"Exported {len(signals)} signals to aapl_signals.csv")
```

---

## 📞 Support

### Documentation Files:
- **QUICKSTART.md** (this file) - Getting started
- **USER_GUIDE.md** - Detailed instructions
- **README.md** - Technical documentation
- **CLIENT_PRESENTATION.md** - Business overview

### Code Comments:
- All code is heavily commented
- Explains the "why" not just the "what"

### Example Output:
- Sample HTML chart included
- Shows what to expect

---

## ✅ Checklist

Before contacting for support, verify:

- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] In correct directory (`cd ~/Desktop/"untitled folder 2"`)
- [ ] Internet connection working (for data download)
- [ ] Correct file permissions
- [ ] Read error messages carefully

---

**You're all set! 🎉**

Run `python3 bxtrender_panel.py` to generate your first analysis!

---

**Last Updated**: November 23, 2025  
**Version**: 2.0  
**Tested on**: macOS Monterey, Ventura, Sonoma

