# Methodology

## 1. Data contract

The core analysis expects a wide price table with a unique, sortable date index and one strictly positive numeric column per asset. Missing or non-finite values are rejected after ingestion. The `yfinance` path explicitly takes the common-date intersection before validation.

The checked-in evidence is synthetic. Optional downloaded prices are exploratory inputs and are not the basis of the repository's public numeric claims.

## 2. Returns and growth

Simple daily return:

\[
r_t=P_t/P_{t-1}-1.
\]

Annualised arithmetic mean:

\[
\bar r_{ann}=252\bar r_d.
\]

Annualised volatility:

\[
\sigma_{ann}=\sqrt{252}\,s_d.
\]

Zero-risk-free Sharpe:

\[
S=\bar r_{ann}/\sigma_{ann}.
\]

Realised CAGR is computed from the compounded wealth path rather than the arithmetic mean:

\[
\mathrm{CAGR}=\left(\prod_t(1+r_t)\right)^{252/n}-1.
\]

The distinction matters because volatility drag makes realised compound growth differ from an annualised arithmetic average.

## 3. Drawdown

For wealth \(W_t\), drawdown is

\[
DD_t=W_t/\max_{s\le t}W_s-1,
\]

and maximum drawdown is the minimum of that path.

## 4. Historical VaR and expected shortfall

For confidence level \(c\), the repository reports the signed lower-tail return quantile

\[
q_{1-c},
\]

and expected shortfall

\[
ES_c=E[r\mid r\le q_{1-c}].
\]

Because these are signed returns, normal loss cases are negative. The repeated-world audit converts them to positive loss magnitudes only for chart readability.

The Gaussian comparator fits sample mean \(\mu\) and standard deviation \(\sigma\):

\[
VaR^{ret}_c=\mu+\sigma z_{1-c},
\]

\[
ES^{ret}_c=\mu-\sigma\frac{\phi(z_{1-c})}{1-c}.
\]

It is a model comparison, not a statement that returns are Gaussian.

## 5. Tail-shape audit

Each world has 1,000 daily returns with annual mean 6% and annual volatility 25%. Gaussian shocks are standard normal. Student-t shocks use 5 degrees of freedom and are scaled by

\[
\sqrt{(\nu-2)/\nu}
\]

so their theoretical variance is one before the common volatility scale is applied.

Two hundred independent worlds are generated per distribution. The report summarises median historical and Gaussian-fitted VaR/ES and the across-world sampling standard deviation of the historical estimators.

This experiment isolates distribution shape. It is not calibrated to any particular stock.

## 6. Rolling co-movement

For each trailing window the correlation matrix is estimated and the mean of its off-diagonal upper-triangle elements is reported. The estimator uses only observations at or before its timestamp.

The known-regime audit generates four assets with calm correlation 0.15 and stress correlation 0.75, alongside a volatility increase. Summary values use only 60-day windows fully contained in a single latent regime so boundary mixtures do not blur the comparison.

## 7. Interpretation limits

- VaR is a quantile threshold, not a measure of losses beyond the threshold.
- ES estimates tail severity but can be noisier because they depend on fewer observations.
- Rolling correlation is an estimator and can move from sampling variation even under constant true correlation.
- The stress-regime results are controlled simulation evidence, not an empirical law of markets.
- None of the reported metrics establishes expected investment performance or an investable strategy.
