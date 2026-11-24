"""Known-truth audits for tail risk and diversification diagnostics."""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import regime_return_panel, return_panel
from metrics import gaussian_var_es, historical_var_es, rolling_mean_correlation

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"


def tail_risk_audit(n_worlds: int = 200, n_days: int = 1000, seed: int = 71) -> pd.DataFrame:
    rows = []
    for dist_name, dist_arg in [("Gaussian", "normal"), ("Student-t(5)", "student_t")]:
        for world in range(n_worlds):
            r = return_panel(["ASSET"], n_days=n_days, annual_mu=0.06,
                             annual_vol=0.25, corr=0.0,
                             distribution=dist_arg, df=5,
                             seed=seed + 10000 * (dist_arg == "student_t") + world)["ASSET"]
            for level in (0.95, 0.99):
                hv, he = historical_var_es(r, level)
                gv, ge = gaussian_var_es(r, level)
                rows.append({
                    "distribution": dist_name,
                    "world": world,
                    "level": level,
                    "hist_var_loss": -hv,
                    "hist_es_loss": -he,
                    "gaussian_var_loss": -gv,
                    "gaussian_es_loss": -ge,
                })
    raw = pd.DataFrame(rows)
    summary = (raw.groupby(["distribution", "level"], as_index=False)
               .agg(hist_var_loss_median=("hist_var_loss", "median"),
                    hist_es_loss_median=("hist_es_loss", "median"),
                    gaussian_var_loss_median=("gaussian_var_loss", "median"),
                    gaussian_es_loss_median=("gaussian_es_loss", "median"),
                    hist_var_sampling_sd=("hist_var_loss", "std"),
                    hist_es_sampling_sd=("hist_es_loss", "std")))
    return summary


def _pure_window_mask(states: pd.Series, window: int, label: str) -> pd.Series:
    x = (states == label).astype(int)
    counts = x.rolling(window).sum()
    return counts.eq(window)


def regime_correlation_audit(n_worlds: int = 100, window: int = 60, seed: int = 91) -> pd.DataFrame:
    rows = []
    names = ["A", "B", "C", "D"]
    for world in range(n_worlds):
        rets, states = regime_return_panel(names, calm_days=500, stress_days=220,
                                           recovery_days=500, calm_corr=0.15,
                                           stress_corr=0.75, calm_vol=0.18,
                                           stress_vol=0.36, seed=seed + world)
        mpc = rolling_mean_correlation(rets, window=window)
        calm_mask = _pure_window_mask(states, window, "calm").reindex(mpc.index, fill_value=False)
        stress_mask = _pure_window_mask(states, window, "stress").reindex(mpc.index, fill_value=False)
        roll_vol = (rets.mean(axis=1).rolling(window).std() * np.sqrt(252)).reindex(mpc.index)
        rows.append({
            "world": world,
            "calm_corr": float(mpc[calm_mask].mean()),
            "stress_corr": float(mpc[stress_mask].mean()),
            "calm_eqw_vol": float(roll_vol[calm_mask].mean()),
            "stress_eqw_vol": float(roll_vol[stress_mask].mean()),
        })
    raw = pd.DataFrame(rows)
    out = pd.DataFrame({
        "metric": ["mean_pairwise_corr", "equal_weight_ann_vol"],
        "calm_median": [raw["calm_corr"].median(), raw["calm_eqw_vol"].median()],
        "stress_median": [raw["stress_corr"].median(), raw["stress_eqw_vol"].median()],
        "stress_minus_calm_median": [
            (raw["stress_corr"] - raw["calm_corr"]).median(),
            (raw["stress_eqw_vol"] - raw["calm_eqw_vol"]).median(),
        ],
        "worlds": [n_worlds, n_worlds],
    })
    return out


def make_figures(tail: pd.DataFrame, regime: pd.DataFrame) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)

    # Tail-shape figure: historical VaR/ES medians at 95% and 99%.
    fig, ax = plt.subplots(figsize=(8, 4.8))
    plot = tail.copy()
    labels = [f"{d}\n{int(l*100)}%" for d, l in zip(plot.distribution, plot.level)]
    x = np.arange(len(plot))
    width = 0.35
    ax.bar(x - width/2, 100 * plot.hist_var_loss_median, width, label="Historical VaR loss")
    ax.bar(x + width/2, 100 * plot.hist_es_loss_median, width, label="Historical ES loss")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Median one-day loss (%)")
    ax.set_title("Same volatility, different tail shape")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES / "tail_shape_var_es.png", dpi=150)
    plt.close(fig)

    # Known-regime calm vs stress co-movement.
    fig2, ax2 = plt.subplots(figsize=(7.5, 4.5))
    row = regime.loc[regime.metric == "mean_pairwise_corr"].iloc[0]
    ax2.bar(["Calm", "Stress"], [row.calm_median, row.stress_median])
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("Median trailing mean pairwise correlation")
    ax2.set_title("Known-regime diversification stress test")
    ax2.grid(axis="y", alpha=0.25)
    fig2.tight_layout()
    fig2.savefig(FIGURES / "regime_correlation_audit.png", dpi=150)
    plt.close(fig2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds-tail", type=int, default=200)
    ap.add_argument("--worlds-regime", type=int, default=100)
    args = ap.parse_args()

    REPORTS.mkdir(parents=True, exist_ok=True)
    tail = tail_risk_audit(n_worlds=args.worlds_tail)
    regime = regime_correlation_audit(n_worlds=args.worlds_regime)
    tail.to_csv(REPORTS / "tail_risk_audit.csv", index=False)
    regime.to_csv(REPORTS / "regime_correlation_audit.csv", index=False)
    make_figures(tail, regime)
    print("Tail-risk audit")
    print(tail.to_string(index=False))
    print("\nRegime-correlation audit")
    print(regime.to_string(index=False))


if __name__ == "__main__":
    main()
