"""Validated price loading plus controlled synthetic return generators."""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def validate_prices(prices: pd.DataFrame, min_rows: int = 30) -> pd.DataFrame:
    if not isinstance(prices, pd.DataFrame) or prices.empty:
        raise ValueError("prices must be a non-empty DataFrame")
    if len(prices) < min_rows:
        raise ValueError(f"at least {min_rows} price rows are required")
    if prices.columns.duplicated().any():
        raise ValueError("duplicate asset columns are not allowed")
    if prices.index.duplicated().any():
        raise ValueError("duplicate dates are not allowed")
    out = prices.sort_index().copy()
    try:
        out = out.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("all price columns must be numeric") from exc
    if not np.isfinite(out.to_numpy()).all():
        raise ValueError("prices contain missing or non-finite values")
    if (out <= 0).any().any():
        raise ValueError("prices must be strictly positive")
    return out


def return_panel(
    names: list[str],
    n_days: int = 2000,
    annual_mu: float = 0.07,
    annual_vol: float = 0.22,
    corr: float = 0.30,
    distribution: str = "normal",
    df: int = 5,
    seed: int = 9,
) -> pd.DataFrame:
    """Controlled simple-return panel with equal marginals and correlation.

    Student-t shocks are scaled to unit variance so normal and heavy-tail
    experiments can hold variance approximately constant.
    """
    if len(names) < 1:
        raise ValueError("at least one asset name is required")
    if n_days < 2:
        raise ValueError("n_days must be at least 2")
    if not -1.0 / max(1, len(names) - 1) < corr < 1.0:
        raise ValueError("correlation is outside the equicorrelation PSD range")
    if annual_vol <= 0:
        raise ValueError("annual_vol must be positive")
    if distribution == "student_t" and df <= 2:
        raise ValueError("Student-t df must exceed 2 for finite variance")

    rng = np.random.default_rng(seed)
    k = len(names)
    corr_m = corr * np.ones((k, k)) + (1.0 - corr) * np.eye(k)
    chol = np.linalg.cholesky(corr_m)

    if distribution == "normal":
        z = rng.standard_normal((n_days, k))
    elif distribution == "student_t":
        z = rng.standard_t(df, size=(n_days, k)) * np.sqrt((df - 2.0) / df)
    else:
        raise ValueError("distribution must be 'normal' or 'student_t'")
    z = z @ chol.T

    daily_mu = annual_mu / TRADING_DAYS
    daily_vol = annual_vol / np.sqrt(TRADING_DAYS)
    rets = daily_mu + daily_vol * z
    if np.any(rets <= -1.0):
        raise RuntimeError("synthetic simple return fell below -100%; change parameters")
    idx = pd.bdate_range("2018-01-02", periods=n_days)
    return pd.DataFrame(rets, index=idx, columns=names)


def regime_return_panel(
    names: list[str],
    calm_days: int = 600,
    stress_days: int = 250,
    recovery_days: int = 600,
    calm_corr: float = 0.15,
    stress_corr: float = 0.75,
    calm_vol: float = 0.18,
    stress_vol: float = 0.36,
    calm_mu: float = 0.07,
    stress_mu: float = -0.18,
    seed: int = 9,
) -> tuple[pd.DataFrame, pd.Series]:
    """Known-regime simple returns and their latent state labels."""
    segments = []
    labels = []
    offset = seed
    specs = [
        ("calm", calm_days, calm_mu, calm_vol, calm_corr),
        ("stress", stress_days, stress_mu, stress_vol, stress_corr),
        ("calm", recovery_days, calm_mu, calm_vol, calm_corr),
    ]
    for i, (state, n, mu, vol, corr) in enumerate(specs):
        part = return_panel(names, n_days=n, annual_mu=mu, annual_vol=vol,
                            corr=corr, seed=offset + 101 * i)
        segments.append(part.reset_index(drop=True))
        labels.extend([state] * n)
    rets = pd.concat(segments, ignore_index=True)
    idx = pd.bdate_range("2018-01-02", periods=len(rets))
    rets.index = idx
    states = pd.Series(labels, index=idx, name="state")
    return rets, states


def returns_to_prices(rets: pd.DataFrame, start_price: float = 100.0) -> pd.DataFrame:
    if start_price <= 0:
        raise ValueError("start_price must be positive")
    if (rets <= -1.0).any().any():
        raise ValueError("simple returns must be greater than -100%")
    return start_price * (1.0 + rets).cumprod()


def synthetic_prices(names, n_days: int = 2000, seed: int = 9) -> pd.DataFrame:
    rets = return_panel(list(names), n_days=n_days, seed=seed)
    return returns_to_prices(rets)


def load_prices(tickers=None, start="2018-01-01", csv: str | None = None,
                synthetic: bool = False, seed: int = 9) -> pd.DataFrame:
    if synthetic:
        names = tickers or ["TECH", "BANK", "ENERGY", "HEALTH"]
        return validate_prices(synthetic_prices(names, seed=seed))
    if csv:
        prices = pd.read_csv(csv, index_col=0, parse_dates=True)
        return validate_prices(prices)
    if not tickers:
        raise ValueError("provide --tickers, --csv or --synthetic")
    import yfinance as yf  # lazy import
    data = yf.download(tickers, start=start, auto_adjust=True, progress=False)["Close"]
    if isinstance(data, pd.Series):
        data = data.to_frame(tickers[0])
    # The analysis uses a common-date panel. Make that choice explicit.
    data = data.dropna(how="any")
    return validate_prices(data)
