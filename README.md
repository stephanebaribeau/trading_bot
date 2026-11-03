# Trading Bot: Gap Scanner & Backtest

A Python learning project to build a day trading bot step by step.
The bot scans stocks for opening gaps and backtests a simple "gap and go"
strategy on historical data.

> ⚠️ **Educational project only. Not financial advice.**
> This bot does not place any real orders.

## What it does

- **Downloads** daily price data from Yahoo Finance using `yfinance`
- **Computes the gap**: how much a stock opens above (or below) the previous day's close
- **Scans** a list of tickers for gaps between +3% and +15%, with price and liquidity filters
- **Backtests** the strategy: buy at the open, exit at the stop-loss, the profit target, or the close

## Project structure

| File              | Description |
|---                |---|
| `essai.py`        | First test: downloads and displays 3 months of AAPL prices |
| `gap.py`          | Cleans the data and computes daily gaps for one stock |
| `scanner.py`      | Scans a list of tickers and returns the gaps that pass the filters |
| `backtest.py`     | Simulates trades on 2 years of data and prints statistics |
| `optimisation.py` | Add parameter optimization with train/test split

## Installation

Requires Python 3.10+.

```bash
git clonei https://github.com/stephanebaribeau/trading_bot.git
cd YOUR-REPO
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python scanner.py    # find recent gaps
python backtest.py   # test the strategy on 2 years of data
```

## Strategy rules

| Parameter                        | Value |
|---                               |---|
| Minimum gap                      | +3% |
| Maximum gap                      | +15% |
| Minimum price                    | $5 |
| Minimum average volume (20 days) | 1,000,000 shares |
| Stop-loss                        | -2% |
| Profit target                    | +4% |
| Slippage                         | 0.05% per side |

## First results

Backtest over 2 years, 15 US stocks:

| Metric           | Result |
|---               |---|
| Trades           | 407 |
| Win rate         | 36.6% |
| Average win      | +2.83% |
| Average loss     | -1.89% |
| **Expectancy**   | **-0.16% per trade** |

**Conclusion:** the strategy loses money in its current form.
55% of the trades hit the stop-loss, which suggests the -2% stop is too
tight for volatile stocks. Next step: test wider stops, while avoiding
overfitting.

## Pitfalls handled

- **Lookahead bias**: the scanner only uses the opening price of the day
  and data from previous days. The 20-day average volume excludes the current day.
- **Slippage**: included in every simulated trade.
- **Stop and target hit on the same day**: daily bars don't show which came
  first, so the backtest assumes the worst case (the stop).

## Known limitations

- **Daily bars only**: intraday price movements are not visible.
- **Survivorship bias**: the ticker list is chosen today, so stocks that
  crashed or were delisted are missing.
- **No commissions** are included yet.

## Roadmap

- [x] Download price data
- [x] Gap scanner
- [x] Basic backtest
- [x] Test different stop-loss levels, with a train/test split to avoid overfitting
- [x] Test the "gap fade" strategy (short the gap, expecting it to fill)
- [x] Add commissions and position sizing
- [x] Intraday data (1–5 minute bars)
- [ ] News and sentiment analysis with AI
- [ ] Paper trading with a broker API

## Disclaimer

This project is for learning purposes only. Trading involves substantial
risk of loss. Past performance in a backtest does not guarantee future results.
