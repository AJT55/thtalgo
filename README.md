# Fair Value Bands Trading System

Exit signal generator using Fair Value Bands.

## Installation

```bash
git clone https://github.com/AJT55/thtalgo.git
cd thtalgo
pip install -r requirements.txt
```

## Usage

```bash
python fair_value_bands_signals.py
```

## Exit Strategy

- **100% Exit**: Daily close breaks 2x deviation band
- **50% Exit**: Weekly close breaks 1x deviation band

All signals wait for candle close confirmation.
