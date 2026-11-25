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

## Notes moved from the README

- The earlier README said skew and kurtosis were there to show that "daily returns are not normal". The checked-in synthetic generator was close to Gaussian, so that sentence overclaimed. Version 0.3 removes it and tests tail shape in the repeated-world audit instead.
- The old `ann_return` label mixed an annualised arithmetic mean with realised compounding. Version 0.3 reports `ann_mean_return` and `cagr` separately. Historical VaR and ES state their sign convention and are reported at 95% and 99%.
- Tail columns are signed returns: `hist_var95_return = -0.03` means a 3% one-day lower-tail threshold. Expected shortfall is the mean return beyond the VaR threshold, so it is normally more negative than VaR.
- At 95% the Student-t(5) world has a slightly smaller median historical VaR than the Gaussian world (2.43% against 2.56%) but a larger ES (3.49% against 3.21%). At 99% the heavy tail dominates both, and the Gaussian-fitted ES (4.19%) understates the Student-t(5) historical ES (5.28%).
- Price inputs are validated for duplicate dates and columns, non-numeric values, missing values and non-positive prices. The optional `yfinance` path uses the common-date intersection across assets.
