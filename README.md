# Trading Bot: Day Trading Strategy Research Lab

A Python learning project to research day trading strategies step by step,
with an honest backtesting process: no lookahead bias, slippage included,
and every parameter choice validated on unseen data.

> ⚠️ **Educational project only. Not financial advice.**
> This bot does not place any real orders.

## Key finding

Four strategy families based on price alone were tested on 15 large US stocks
over 5 years. **None of them showed a real edge** once tested on unseen data.

Adding pre-market news changed the picture: Opening Range Breakout trades on
days with an **analyst downgrade or price target cut** were positive in
training, in testing, and in every single year from 2021 to 2026
(+0.126R per trade over 502 trades). This result was discovered, not predicted,
so it is now being validated on new data through paper trading
(see [Pre-registered strategy](#pre-registered-strategy-forward-test)).

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
| `nouvelles_test.py` | First look at Alpaca news: timing, number of symbols per article |
| `donnees_nouvelles.py` | Downloads 5 years of news from Alpaca (Benzinga), with a local CSV cache |
| `orb_nouvelles.py` | ORB results by number of pre-market news articles |
| `categories.py` | Keyword-based news classifier, with a sample check of each category |
| `orb_categories.py` | ORB results by news category |
| `verif_baisse.py` | Robustness checks on the analyst downgrade result |
| `paper_test.py` | Connection test for the Alpaca paper trading account: account, clock, test order |
| `test_oto.py` | Checks that Alpaca accepts an OTO order with a stop entry |
| `bot.py` | Paper trading bot that runs the pre-registered strategy each trading day |
| `tout_fermer.py` | Emergency script: cancels all orders and closes all positions |

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

### 5. News before the open

For each trading day, only **targeted** news (2 symbols or fewer) published
between 4 p.m. the previous trading day and 9:30 a.m. were used. News published
during the session often describes price moves instead of causing them.

**Number of news articles: no effect.** Days with 0, 1–2, or 3+ articles all
showed about -0.005R in training.

**News category: a clear difference.** Headlines were classified with keyword
rules, checked on random samples, then frozen before looking at trading results.

| Category | Train trades | Train expectancy | Test trades | Test expectancy |
|---|---|---|---|---|
| No news (reference) | 5,699 | -0.003R | 2,303 | -0.030R |
| **Analyst downgrade / price target cut** | 373 | **+0.114R** | 129 | **+0.159R** |
| Earnings results | 230 | +0.076R | 101 | +0.051R |
| Neutral analyst action | 323 | +0.035R | 159 | -0.092R |
| Analyst upgrade / price target raise | 580 | +0.011R | 234 | -0.071R |
| Other news | 3,567 | -0.018R | 2,017 | -0.071R |

The initial hypothesis was the **opposite**: upgrades were expected to help
a long breakout, and downgrades to hurt it.

### 6. Robustness checks on the downgrade result

- **By year**: positive in all 6 years (from +0.074R in 2024 to +0.208R in 2023).
- **By ticker**: 10 of 15 tickers positive. Still +0.08R per trade after
  removing the three best tickers.
- **Not driven by earnings**: +0.136R on the 421 downgrade days without earnings news.
- **By gap direction**: gap down +0.151R, flat +0.165R, gap up +0.026R.
  Gap-up days are weak, consistent with the failed "gap and go" strategy.

## Pre-registered strategy (forward test)

**Registered on November 21, 2026, before any forward test trade.**
These rules are frozen. Any change will be recorded below as a new version,
and its results will be counted separately.


## Paper trading bot

`bot.py` runs the pre-registered strategy on an Alpaca **paper** account
(simulated money). It is started each trading day before 9:46 a.m. ET and
stays open until the close.

1. Checks the Alpaca market calendar (holidays, early closes).
2. Waits until 9:46 a.m. ET, one minute after the opening range is complete.
3. Finds targeted analyst downgrade news published between 4 p.m. the previous
   trading day and 9:30 a.m.
4. For each candidate, computes the opening range and the position size,
   then sends one **OTO order**: a buy stop above the range high, which
   triggers a stop-loss at the range low once filled.
5. Five minutes before the actual close, cancels all orders and closes
   all positions.
6. Logs every event in `journal_paper.csv`.

```bash
python bot.py               # normal run
python bot.py --test AAPL   # forces a 1-share trade on AAPL, without the news filter
python tout_fermer.py       # emergency: cancel all orders and close all positions
```

### Implementation notes

Added on November 23, 2026, before the first forward test trade.
These notes describe how the frozen rules are executed. They do not change them.

- **Live data feed**: the free Alpaca plan only provides real-time data from
  the IEX exchange. The live opening range is computed from IEX bars, while
  the backtest used consolidated (SIP) data. The range high and low may differ
  by a few cents.
- **Entry price**: the buy stop is placed $0.01 above the range high, matching
  the backtest rule "price strictly above the high". If the price is already
  above the high at 9:46 a.m., the bot buys at market, like the backtest
  entering at the bar's open.
- **Early closes**: positions are closed 5 minutes before the actual close
  from the Alpaca calendar (12:55 p.m. on 1 p.m. early-close days).
- **Position cap**: the 25% maximum position size often applies before the 1%
  risk limit on stocks with a narrow opening range. Results are measured in R,
  so this does not change the expectancy, only the dollar amounts.
- **No leverage**: position sizes are based on account equity, never on the
  margin buying power offered by the broker.


### Rules (version 1)

1. **Universe**: AAPL, NVDA, AMD, TSLA, META, PLTR, COIN, MU, SOFI, MARA,
   RIVN, SNAP, UBER, SHOP, NFLX.
2. **News filter**: at least one Alpaca/Benzinga article mentioning 2 symbols
   or fewer, published between 4:00 p.m. ET the previous trading day and
   9:30 a.m. ET, whose headline matches `\bdowngrade[sd]?\b|lowers price target`
   (option alerts excluded), as defined in `categories.py`.
3. **Opening range**: high and low of the first 15 minutes (9:30 to 9:45 a.m. ET).
4. **Entry**: buy when the price breaks above the opening range high,
   from 9:45 a.m. onward. Long only, one trade per stock per day.
5. **Stop**: the opening range low.
6. **Exit**: at the stop, or at the market close.
7. **Position size**: risk 1% of the account per trade, with a maximum
   position of 25% of the account.
8. **No other filter.** In particular, gap-up days are **not** excluded,
   even though they were weak in the backtest. This idea may be tested
   later as a separate hypothesis.

### Backtest reference

| | Trades | Expectancy |
|---|---|---|
| Train (2021–2024) | 373 | +0.114R |
| Test (2025–2026) | 129 | +0.159R |
| All years | 502 | +0.126R |

About 85 trades per year are expected.

### Evaluation plan

- **First 3 months**: check the execution only. Do orders fill as expected?
  Is the real slippage close to the 0.05% per side assumed in the backtest?
  About 20 trades are expected: far too few to judge the strategy.
- **Decision after at least 80 forward trades** (about one year):
  - expectancy after commissions **above 0**: the strategy passes the forward test;
  - expectancy **below 0**: the strategy is rejected.
- No real money before the forward test is passed.
- 
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
- [x] News data and keyword classification
- [x] Robustness checks on the analyst downgrade result
- [x] Pre-registration of the strategy rules
- [x] Paper trading bot with the Alpaca API
- [ ] Forward test evaluation (at least 80 trades)
- [ ] AI news classification (compare with keyword rules)

## Disclaimer

This project is for learning purposes only. Trading involves substantial
risk of loss. Past performance in a backtest does not guarantee future results.