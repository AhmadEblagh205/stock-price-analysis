import math
from statistics import NormalDist

import numpy as np
import pandas as pd
import pytest

from data import regime_return_panel, return_panel, synthetic_prices, validate_prices
from metrics import (
    cagr_from_returns,
    gaussian_var_es,
    historical_var_es,
    max_drawdown,
    rolling_mean_correlation,
    summary_table,
)


def test_historical_var_es_known_small_sample():
    x = pd.Series([-0.10, -0.05, 0.00, 0.05, 0.10])
    var, es = historical_var_es(x, level=0.80)
    assert var == pytest.approx(-0.06)
    assert es == pytest.approx(-0.10)


def test_gaussian_var_es_matches_closed_form():
    x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0]) / 100
    level = 0.95
    var, es = gaussian_var_es(x, level)
    mu = x.mean()
    sd = x.std(ddof=1)
    alpha = 1 - level
    z = NormalDist().inv_cdf(alpha)
    phi = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    assert var == pytest.approx(mu + sd * z)
    assert es == pytest.approx(mu - sd * phi / alpha)
    assert es < var


def test_cagr_and_drawdown_known_paths():
    daily = np.repeat(0.01, 252)
    assert cagr_from_returns(daily) == pytest.approx(1.01 ** 252 - 1.0)
    assert max_drawdown([0.10, -0.20, 0.05]) == pytest.approx(-0.20)


def test_summary_table_has_explicit_growth_and_tail_columns():
    prices = synthetic_prices(["X", "Y"], n_days=500, seed=1)
    rets = prices.pct_change(fill_method=None).dropna()
    t = summary_table(rets)
    required = {
        "ann_mean_return", "cagr", "ann_vol", "sharpe_rf0", "skew",
        "excess_kurtosis", "best_day", "worst_day", "max_drawdown",
        "hist_var95_return", "hist_es95_return",
        "hist_var99_return", "hist_es99_return",
    }
    assert required.issubset(t.columns)
    assert (t["ann_vol"] > 0).all()
    assert (t["hist_es95_return"] <= t["hist_var95_return"]).all()
    assert (t["hist_es99_return"] <= t["hist_var99_return"]).all()
    assert (t["max_drawdown"] <= 0).all()


def test_rolling_correlation_is_trailing_and_future_safe():
    rng = np.random.default_rng(4)
    a = rng.normal(size=200)
    rets = pd.DataFrame({"A": a, "B": a + rng.normal(scale=0.05, size=200)})
    base = rolling_mean_correlation(rets, window=40)
    changed = rets.copy()
    changed.iloc[150:, 1] *= -1
    new = rolling_mean_correlation(changed, window=40)
    # Outputs ending before the perturbation cannot change.
    pd.testing.assert_series_equal(base.iloc[:111], new.iloc[:111])


def test_rolling_correlation_requires_two_assets():
    with pytest.raises(ValueError):
        rolling_mean_correlation(pd.DataFrame({"A": np.arange(100.0)}), window=20)


def test_price_validation_rejects_bad_inputs():
    idx = pd.date_range("2025-01-01", periods=40)
    good = pd.DataFrame({"A": np.linspace(100, 120, 40)}, index=idx)
    out = validate_prices(good)
    assert out.equals(good.astype(float))

    bad = good.copy()
    bad.iloc[3, 0] = 0.0
    with pytest.raises(ValueError):
        validate_prices(bad)

    dup = pd.concat([good.iloc[:1], good]).sort_index()
    with pytest.raises(ValueError):
        validate_prices(dup)


def test_synthetic_generator_is_reproducible():
    a = return_panel(["A", "B"], n_days=100, seed=7)
    b = return_panel(["A", "B"], n_days=100, seed=7)
    pd.testing.assert_frame_equal(a, b)


def test_known_regime_has_higher_stress_correlation():
    rets, states = regime_return_panel(["A", "B", "C", "D"], seed=13)
    mpc = rolling_mean_correlation(rets, window=60)
    calm = (states.eq("calm").astype(int).rolling(60).sum().eq(60)).reindex(mpc.index, fill_value=False)
    stress = (states.eq("stress").astype(int).rolling(60).sum().eq(60)).reindex(mpc.index, fill_value=False)
    assert mpc[stress].mean() > mpc[calm].mean() + 0.35


def test_heavy_tail_99_es_exceeds_gaussian_same_variance():
    normal = return_panel(["A"], n_days=50_000, annual_vol=0.25,
                          distribution="normal", seed=10)["A"]
    heavy = return_panel(["A"], n_days=50_000, annual_vol=0.25,
                         distribution="student_t", df=5, seed=10)["A"]
    _, es_n = historical_var_es(normal, level=0.99)
    _, es_t = historical_var_es(heavy, level=0.99)
    assert -es_t > -es_n * 1.15
