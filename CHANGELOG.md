# Changelog

## 0.3.0 — defensibility and risk-diagnostics audit

- separated annualised arithmetic mean return from realised CAGR;
- added maximum drawdown and explicit 95%/99% historical VaR/ES return conventions;
- added a Gaussian VaR/ES comparator with a closed-form implementation;
- added validated price-ingestion contracts and explicit common-date alignment;
- hardened rolling correlation for invalid windows/single-asset inputs;
- added a 200-world Gaussian-vs-Student-t tail-shape experiment;
- added a 100-world known-regime diversification/correlation stress test;
- removed the unsupported claim that the old synthetic skew/kurtosis established non-normal market returns;
- added `docs/METHODOLOGY.md`;
- expanded tests from 2 to 12.

## 0.2.0, update round 4

Added historical VaR 95 and expected shortfall columns to the summary table, and a rolling 60 day mean pairwise correlation chart showing that diversification is not constant.

## 0.1.0

Initial release.
