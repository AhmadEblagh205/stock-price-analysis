# Stock Return, Tail-Risk & Diversification Laboratory

[![CI](https://github.com/AhmadEblagh205/stock-price-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/AhmadEblagh205/stock-price-analysis/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

I first built an exploratory version of this as a guided Dataquest project. This rebuild is my own. It states its statistical conventions and tests VaR, expected shortfall and diversification claims on simulated data where the answer is known. It is an independent educational project, not investment advice and not evidence of professional portfolio-management experience. The checked-in reports use synthetic data. Real prices can be supplied as a CSV or downloaded with `yfinance`, which is optional.

## What it does

- Reports per asset the annualised mean return, CAGR, volatility, zero-risk-free Sharpe ratio, skew and excess kurtosis, best and worst day, and maximum drawdown.
- Reports historical 95% and 99% VaR and expected shortfall as signed return thresholds in `reports/summary_stats.csv`.
- Plots growth of one unit invested, rolling volatility, drawdowns, a correlation matrix and trailing mean pairwise correlation.
- Runs two repeated-world audits on simulated data (`python src/audit.py`).

## Results

Both audits use simulated data, not market prices.

The first audit compares 200 worlds of 1,000 days each, with Gaussian returns and with Student-t(5) returns. Both have a 6% annual mean and 25% volatility. Median loss magnitudes:

| Distribution | Level | Historical VaR | Historical ES | Gaussian-fitted ES |
|---|---:|---:|---:|---:|
| Gaussian | 95% | 2.56% | 3.21% | 3.22% |
| Student-t(5) | 95% | 2.43% | 3.49% | 3.23% |
| Gaussian | 99% | 3.59% | 4.14% | 4.17% |
| Student-t(5) | 99% | 3.99% | 5.28% | 4.19% |

With the same volatility, the heavier tail gives a larger ES, and at 99% a larger VaR as well. A Gaussian fit understates the Student-t(5) ES at 99%.

The second audit generates four assets with a calm, stress, calm regime. Pairwise correlation is 0.15 in calm and 0.75 in stress, and annual volatility is 18% and 36%. Across 100 worlds, using only 60-day windows inside one regime, the median trailing mean pairwise correlation was 0.146 in calm against 0.746 in stress. The median equal-weight annualised volatility was 0.108 against 0.323. This shows the rolling-correlation measure can recover a designed loss of diversification. It says nothing about the parameters of any real market.

## How to run

```bash
pip install -r requirements.txt

# Reproduce the checked-in synthetic descriptive report
python src/analyze.py --synthetic --seed 9

# Repeated-world audits
python src/audit.py

# Real market input, exploratory only
python src/analyze.py --tickers AAPL MSFT JPM XOM --start 2018-01-01

# Or supply your own wide price CSV: date index + one column per asset
python src/analyze.py --csv path/to/prices.csv

pytest -q
```

There are 12 tests. They cover exact VaR and ES examples, Gaussian closed-form checks, CAGR and drawdown definitions, summary columns, rolling correlation using only past data, price validation, reproducible synthetic data, recovery of the stress regime and heavy-tail ES behaviour.

## Notes

The earlier version overclaimed that skew and kurtosis showed returns are not normal, and it mixed an arithmetic mean with CAGR under one label. Version 0.3 fixes both. The details, the definitions and the audit design are in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Licence

MIT, see [LICENSE](LICENSE).
