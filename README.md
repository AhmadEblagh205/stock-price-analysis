# Stock Return, Tail-Risk & Diversification Laboratory

[![CI](https://github.com/AhmadEblagh205/stock-price-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/AhmadEblagh205/stock-price-analysis/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A compact market-risk analysis project covering realised growth, volatility, drawdowns, tail risk and co-movement. I first built an exploratory version as a guided Dataquest project; this rebuild makes the statistical conventions explicit and adds **known-truth stress tests** so claims about VaR/ES and diversification are checked under controlled data-generating processes rather than inferred from one chart.

This is an **independent educational/research project**, not investment advice and not evidence of professional portfolio-management experience. The checked-in reports use synthetic data. Real market prices can be supplied through CSV or downloaded optionally with `yfinance`.

## What the main analysis reports

For each asset, `reports/summary_stats.csv` separates quantities that are often blurred together:

- annualised arithmetic mean return;
- realised CAGR;
- annualised volatility;
- zero-risk-free Sharpe ratio;
- skew and excess kurtosis;
- best/worst day;
- maximum drawdown;
- historical 95% and 99% VaR/expected-shortfall **return thresholds**.

The tail columns are signed returns: for example `hist_var95_return = -0.03` means a 3% one-day lower-tail threshold. Expected shortfall is the mean return conditional on being beyond the VaR threshold, so it should normally be more negative than VaR.

The figures show growth of one unit invested, rolling volatility, drawdowns, a correlation matrix and trailing mean pairwise correlation. Rolling correlation is an estimator, not proof that correlation must rise in every sell-off; the controlled regime experiment below is what tests that mechanism directly.

## Audit 1 — same volatility, different tails

`python src/audit.py` repeats 200 independent 1,000-day worlds under two one-asset data-generating processes with the **same annual mean (6%) and variance scale (25% volatility)**:

- Gaussian daily returns;
- Student-t(5) daily returns scaled to unit variance before applying the same volatility.

Median loss magnitudes across the repeated worlds are:

| Distribution | Level | Historical VaR | Historical ES | Gaussian-fitted ES |
|---|---:|---:|---:|---:|
| Gaussian | 95% | 2.56% | 3.21% | 3.22% |
| Student-t(5) | 95% | 2.43% | 3.49% | 3.23% |
| Gaussian | 99% | 3.59% | 4.14% | 4.17% |
| Student-t(5) | 99% | 3.99% | 5.28% | 4.19% |

The useful result is not that one number is universally “better”. At 95%, the heavier-tailed distribution is more sharply concentrated near the centre, so its VaR can actually look slightly *smaller* while its ES is worse. At 99%, the heavy tail dominates both. A Gaussian fit also materially understates the Student-t(5) 99% ES in this controlled experiment.

That is why this repository treats VaR as a threshold diagnostic and ES as a complementary tail-severity diagnostic rather than summarising risk with one scalar.

## Audit 2 — known-regime diversification stress

A second repeated experiment generates four assets with a latent calm/stress/calm regime:

- calm pairwise correlation: **0.15**;
- stress pairwise correlation: **0.75**;
- calm annual volatility: 18%;
- stress annual volatility: 36%.

Across 100 independent worlds, considering only 60-day windows entirely inside a regime:

- median trailing mean pairwise correlation: **0.146 calm vs 0.746 stress**;
- median equal-weight annualised volatility: **0.108 calm vs 0.323 stress**.

This is deliberately a known-truth simulation. It demonstrates that the rolling-correlation diagnostic can recover a designed loss of diversification; it does **not** claim that every real market drawdown has those parameters.

## Important corrections from the earlier version

The earlier README said skew/kurtosis were there to demonstrate that “daily returns are not normal”. The checked-in synthetic generator was close to Gaussian, so that sentence overclaimed what the evidence showed. V0.3 removes it and tests tail shape explicitly instead.

The old `ann_return` label also mixed an annualised arithmetic mean with realised compounding. V0.3 reports `ann_mean_return` and `cagr` separately. Historical VaR/ES now state their sign convention explicitly and are reported at both 95% and 99% levels.

Price inputs are validated for duplicate dates/columns, non-numeric values, missing values and non-positive prices. The optional `yfinance` path uses the common-date intersection across assets rather than silently mixing unmatched observations.

## Usage

```bash
pip install -r requirements.txt

# Reproduce the checked-in synthetic descriptive report
python src/analyze.py --synthetic --seed 9

# Controlled repeated-world audits
python src/audit.py

# Real market input, exploratory only
python src/analyze.py --tickers AAPL MSFT JPM XOM --start 2018-01-01

# Or supply your own wide price CSV: date index + one column per asset
python src/analyze.py --csv path/to/prices.csv
```

## Tests

```bash
pytest -q
```

V0.3 has **12 tests** covering exact VaR/ES examples, Gaussian closed-form checks, CAGR/drawdown definitions, explicit summary columns, trailing/future-safe rolling correlation, price validation, reproducible synthetic data, recovery of the known stress-correlation regime and heavy-tail ES behaviour.

See [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) for definitions and audit design.

## Licence

MIT, see [LICENSE](LICENSE).
