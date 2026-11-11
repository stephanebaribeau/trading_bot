# Trading Bot: Day Trading Strategy Research Lab

A Python learning project to research day trading strategies step by step,
with an honest backtesting process: no lookahead bias, slippage included,
and every parameter choice validated on unseen data.

> ⚠️ **Educational project only. Not financial advice.**
> This bot does not place any real orders.

## Key finding

Four strategy families were tested on 15 large US stocks over 5 years.
**None of them showed a real edge** once tested on unseen data.
The most valuable output of this project is the testing framework itself,
which caught several results that looked profitable but were only luck.

## Project structure

| File | Description |
|---|---|
| `essai.py` | First test: downloads 3 months of AAPL prices with yfinance |
| `gap.py` | Computes daily opening gaps for one stock |
| `scanner.py` | Gap scanner with price and liquidity filters, plus a shared download function |
| `backtest.py` | First "gap and go" backtest on daily bars |
| `optimisation.py` | Grid search on stop-loss and profit target, with a train/test split |
| `fade.py` | Tests the opposite strategy: shorting the gap, expecting it to fill |
| `capital.py` | Simulates a $10,000 account with position sizing, commissions, and a SPY comparison |
| `intraday.py` | First look at 5-minute bars and the opening range |
| `classement.py` | Ranks tickers by liquidity, intraday range, and breakout behaviour |
| `orb.py` | Opening Range Breakout (ORB) simulation, bar by bar |
| `alpaca_test.py` | Connection test for the Alpaca market data API |
| `donnees_alpaca.py` | Downloads 5 years of 5-minute bars from Alpaca, with a local CSV cache |
| `orb_alpaca.py` | ORB backtest on 5 years of data, with a train/test split and yearly results |
| `orb_pistes.py` | Tests two ORB variants: a 5-minute opening range and a relative volume filter |

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/stephanebaribeau/trading_bot.git
cd trading_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Alpaca setup (for the intraday scripts)

1. Create a free account at [alpaca.markets](https://alpaca.markets) and switch to the **Paper Trading** account.
2. Generate API keys.
3. Create a `.env` file at the project root:

```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
```

The `.env` file is listed in `.gitignore`. **Never commit your API keys.**

## Methodology

- **Train/test split**: parameters are chosen on 2021–2024 only, then validated
  **once** on 2025–2026. The test period is never used to tune anything.
- **Results in R**: intraday results are measured in units of risk
  (1R = distance from entry to stop), which makes trades with different stop
  distances comparable.
- **Slippage**: 0.05% per side on every simulated trade.
- **Worst case assumptions**: when a bar touches both the stop and the target,
  the stop is assumed to come first. A stop hit by a price gap exits at the
  worse open price.

## Results

### 1. Gap and go (daily bars, 5 years)

Buy stocks that open 3–15% above the previous close, then exit at a stop,
a target, or the close.

- All 20 stop/target combinations lost money on the training period.
- Best combination (stop 6%, target 8%): **-0.141% per trade** in training,
  **-0.138%** in testing.
- With position sizing and commissions ($10,000 account, top 3 gaps per day):
  **-21.09%** in training. In testing: **+4.00%** vs **+30.86%** for buy-and-hold SPY.
- The top-3 rule looked good in testing but failed in training: luck, not edge.

### 2. Gap fade (short the gap, daily bars)

- After a gap, stocks moved only **-0.059%** on average from open to close,
  less than the 0.10% round-trip slippage.
- 51.4% closed below the open: essentially a coin flip.
- Best stop (6%): **-0.158% per trade** in training, **-0.068%** in testing.
- Long and short both lose: a sign there is no exploitable edge, only costs.

### 3. Opening Range Breakout, 15-minute range (5-minute bars)

Buy when the price breaks the high of the first 15 minutes. Stop at the low
of the range, exit at the stop or the close.

| Period | Trades | Win rate | Avg win | Avg loss | Expectancy |
|---|---|---|---|---|---|
| Train (2021–2024) | 9,722 | 45.1% | +0.93R | -0.77R | **-0.005R** |
| Test (2025–2026) | 4,482 | 43.4% | +0.84R | -0.73R | **-0.048R** |

- Break-even before commissions, so losing after commissions.
- On only 59 days of yfinance data, the same strategy showed -0.122R.
  The 5-year data showed this period was simply the worst one:
  short samples are misleading.
- The first 15 minutes contain about half of the day's range, so the stop
  is wide and little movement is left to capture.

### 4. ORB variants

Both variants were chosen from the diagnosis **before** seeing the results,
and the volume threshold (2x the 20-day average) was fixed in advance.

| Range | Volume filter | Train trades | Win rate | Expectancy (train) |
|---|---|---|---|---|
| 5 min | Yes | 691 | 42.4% | +0.044R |
| 15 min | No | 9,550 | 45.1% | -0.009R |
| 15 min | Yes | 561 | 46.9% | -0.009R |
| 5 min | No | 10,990 | 36.9% | -0.068R |

- Best combination in testing: **-0.012R** (284 trades). It does not hold.
- The volume filter helped only with the 5-minute range, which suggests chance.

## Pitfalls handled

- **Lookahead bias**: indicators use only past data (`shift(1)` before rolling
  averages). Intraday bars are labelled by their **start** time, so the
  15-minute range is only known at 9:45, not 9:40.
- **Overfitting**: few parameter combinations, chosen from a diagnosis,
  validated once on unseen data.
- **Small samples**: 59 days of data gave a misleading picture that 5 years corrected.
- **Bugs that produce no error**: identical results for different settings
  revealed a parameter that was not passed through.

## Known limitations

- **Survivorship bias**: the ticker list was chosen in 2026, so stocks that
  crashed or were delisted are missing.
- **Commissions** are included only in `capital.py`.
- **No short borrowing costs** in the gap fade backtest.
- **Half trading days** (early close at 1 p.m.) keep extended-hours bars
  until 3:55 p.m. Impact: about 3 days per year.
- Trades on different stocks on the same day are correlated, so the
  effective sample size is smaller than the number of trades.

## Roadmap

- [x] Download price data and build a gap scanner
- [x] Daily backtest with stop-loss and profit target
- [x] Parameter optimization with a train/test split
- [x] Gap fade strategy (short)
- [x] Position sizing, commissions, and SPY comparison
- [x] Intraday data (5-minute bars) and Opening Range Breakout
- [x] 5 years of intraday history with Alpaca
- [x] ORB variants: 5-minute range and relative volume filter
- [ ] News and sentiment analysis with AI
- [ ] Paper trading with the Alpaca API

## Disclaimer

This project is for learning purposes only. Trading involves substantial
risk of loss. Past performance in a backtest does not guarantee future results.