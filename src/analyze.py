"""Exploratory stock-return analysis: growth, risk, drawdowns and co-movement.

Usage:
    python src/analyze.py --synthetic
    python src/analyze.py --tickers AAPL MSFT JPM XOM --start 2018-01-01
    python src/analyze.py --csv data/prices.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import load_prices
from metrics import rolling_mean_correlation, summary_table

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--tickers", nargs="+")
    mode.add_argument("--csv")
    mode.add_argument("--synthetic", action="store_true")
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--seed", type=int, default=9)
    args = ap.parse_args()

    prices = load_prices(args.tickers, start=args.start, csv=args.csv,
                         synthetic=args.synthetic, seed=args.seed)
    rets = prices.pct_change(fill_method=None).dropna(how="any")
    FIGURES.mkdir(parents=True, exist_ok=True)

    # 1. Growth of one unit invested.
    cum = (1.0 + rets).cumprod()
    fig, ax = plt.subplots(figsize=(9, 5))
    for c in cum.columns:
        ax.plot(cum.index, cum[c], lw=1.6, label=c)
    ax.set(title="Growth of 1 unit invested", ylabel="Value")
    ax.legend(); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(FIGURES / "cumulative_returns.png", dpi=150)

    # 2. Rolling annualised volatility.
    roll_vol = rets.rolling(30).std() * np.sqrt(252)
    fig2, ax2 = plt.subplots(figsize=(9, 4.5))
    for c in roll_vol.columns:
        ax2.plot(roll_vol.index, roll_vol[c], lw=1.3, label=c)
    ax2.set(title="Rolling 30-day annualised volatility", ylabel="Volatility")
    ax2.legend(); ax2.grid(alpha=0.3)
    fig2.tight_layout(); fig2.savefig(FIGURES / "rolling_volatility.png", dpi=150)

    # 3. Drawdowns.
    dd = cum / cum.cummax() - 1.0
    fig3, ax3 = plt.subplots(figsize=(9, 4.5))
    for c in dd.columns:
        ax3.plot(dd.index, dd[c], lw=1.3, label=c)
    ax3.set(title="Drawdown from running peak", ylabel="Drawdown")
    ax3.legend(); ax3.grid(alpha=0.3)
    fig3.tight_layout(); fig3.savefig(FIGURES / "drawdowns.png", dpi=150)

    # 4. Correlation matrix.
    corr = rets.corr()
    fig4, ax4 = plt.subplots(figsize=(5.5, 5))
    im = ax4.imshow(corr, vmin=-1, vmax=1)
    ax4.set_xticks(range(len(corr)), corr.columns, rotation=45, ha="right")
    ax4.set_yticks(range(len(corr)), corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax4.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig4.colorbar(im, shrink=0.8)
    ax4.set_title("Daily return correlations")
    fig4.tight_layout(); fig4.savefig(FIGURES / "correlations.png", dpi=150)

    # 5. Trailing mean pairwise correlation.
    if rets.shape[1] >= 2 and len(rets) >= 60:
        mpc = rolling_mean_correlation(rets)
        fig5, ax5 = plt.subplots(figsize=(9, 4.2))
        ax5.plot(mpc.index, mpc, lw=1.6)
        ax5.axhline(mpc.mean(), ls="--", lw=1, label=f"average {mpc.mean():.2f}")
        ax5.set(ylabel="Mean pairwise correlation (60d)",
                title="Rolling co-movement")
        ax5.legend(); ax5.grid(alpha=0.3)
        fig5.tight_layout(); fig5.savefig(FIGURES / "rolling_correlation.png", dpi=150)

    plt.close("all")
    table = summary_table(rets).round(4)
    REPORTS.mkdir(parents=True, exist_ok=True)
    table.to_csv(REPORTS / "summary_stats.csv")
    print(table.to_string())
    print(f"\nSaved table -> {REPORTS / 'summary_stats.csv'}")
    print(f"Figures -> {FIGURES}")


if __name__ == "__main__":
    main()
