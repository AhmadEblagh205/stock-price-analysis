"""Return, drawdown, tail-risk and co-movement metrics.

The functions in this module are intentionally small and dependency-light so
that the numerical conventions are explicit and unit-testable.
"""
from __future__ import annotations

from math import exp, pi, sqrt
from statistics import NormalDist

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _clean_series(values: pd.Series | np.ndarray) -> np.ndarray:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if x.size < 2:
        raise ValueError("at least two finite returns are required")
    return x


def historical_var_es(values: pd.Series | np.ndarray, level: float = 0.95) -> tuple[float, float]:
    """Historical lower-tail return VaR and expected shortfall.

    Returns are *signed return thresholds*, so losses are normally negative.
    For example, ``var=-0.03`` means a 3% one-day loss threshold.  This avoids
    hiding the sign convention inside a positive 'loss magnitude'.
    """
    if not 0.5 < level < 1.0:
        raise ValueError("level must lie strictly between 0.5 and 1")
    x = _clean_series(values)
    q = float(np.quantile(x, 1.0 - level))
    tail = x[x <= q]
    es = float(tail.mean()) if tail.size else q
    return q, es


def gaussian_var_es(values: pd.Series | np.ndarray, level: float = 0.95) -> tuple[float, float]:
    """Gaussian lower-tail return VaR and ES fitted to sample mean/SD."""
    if not 0.5 < level < 1.0:
        raise ValueError("level must lie strictly between 0.5 and 1")
    x = _clean_series(values)
    mu = float(np.mean(x))
    sigma = float(np.std(x, ddof=1))
    if sigma <= 0:
        raise ValueError("return standard deviation must be positive")
    alpha = 1.0 - level
    z = NormalDist().inv_cdf(alpha)
    phi = exp(-0.5 * z * z) / sqrt(2.0 * pi)
    var = mu + sigma * z
    es = mu - sigma * phi / alpha
    return float(var), float(es)


def cagr_from_returns(values: pd.Series | np.ndarray, trading_days: int = TRADING_DAYS) -> float:
    """Realised compound annual growth rate from simple daily returns."""
    x = _clean_series(values)
    if np.any(x <= -1.0):
        raise ValueError("simple returns must be greater than -100%")
    growth = float(np.prod(1.0 + x))
    years = x.size / float(trading_days)
    return growth ** (1.0 / years) - 1.0


def max_drawdown(values: pd.Series | np.ndarray) -> float:
    """Maximum peak-to-trough drawdown of a simple-return series."""
    x = _clean_series(values)
    if np.any(x <= -1.0):
        raise ValueError("simple returns must be greater than -100%")
    wealth = np.cumprod(1.0 + x)
    peaks = np.maximum.accumulate(np.r_[1.0, wealth])
    dd = np.r_[1.0, wealth] / peaks - 1.0
    return float(dd.min())


def rolling_mean_correlation(rets: pd.DataFrame, window: int = 60) -> pd.Series:
    """Trailing mean pairwise correlation across all columns."""
    if not isinstance(rets, pd.DataFrame) or rets.shape[1] < 2:
        raise ValueError("rolling correlation requires at least two assets")
    if window < 2 or window > len(rets):
        raise ValueError("window must be between 2 and the number of rows")
    if not np.isfinite(rets.to_numpy(dtype=float)).all():
        raise ValueError("returns contain non-finite values")

    n = rets.shape[1]
    out: list[float] = []
    for i in range(window, len(rets) + 1):
        c = rets.iloc[i - window:i].corr().to_numpy(dtype=float)
        off_diag = c[np.triu_indices(n, k=1)]
        out.append(float(np.nanmean(off_diag)))
    return pd.Series(out, index=rets.index[window - 1:], name="mean_pairwise_corr")


def summary_table(rets: pd.DataFrame, trading_days: int = TRADING_DAYS) -> pd.DataFrame:
    """Return/risk summary with explicit arithmetic and compound growth."""
    if not isinstance(rets, pd.DataFrame) or rets.empty:
        raise ValueError("returns must be a non-empty DataFrame")
    if not np.isfinite(rets.to_numpy(dtype=float)).all():
        raise ValueError("returns contain non-finite values")
    if (rets <= -1.0).any().any():
        raise ValueError("simple returns must be greater than -100%")

    ann_mean = rets.mean() * trading_days
    ann_vol = rets.std(ddof=1) * np.sqrt(trading_days)
    out = pd.DataFrame(index=rets.columns)
    out["ann_mean_return"] = ann_mean
    out["cagr"] = [cagr_from_returns(rets[c], trading_days) for c in rets]
    out["ann_vol"] = ann_vol
    out["sharpe_rf0"] = ann_mean / ann_vol
    out["skew"] = rets.skew()
    out["excess_kurtosis"] = rets.kurtosis()
    out["best_day"] = rets.max()
    out["worst_day"] = rets.min()
    out["max_drawdown"] = [max_drawdown(rets[c]) for c in rets]

    for level, tag in [(0.95, "95"), (0.99, "99")]:
        pairs = [historical_var_es(rets[c], level=level) for c in rets]
        out[f"hist_var{tag}_return"] = [p[0] for p in pairs]
        out[f"hist_es{tag}_return"] = [p[1] for p in pairs]

    return out
