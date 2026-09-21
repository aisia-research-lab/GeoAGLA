#!/usr/bin/env python3
"""02_analyze_e10_ablation.py
==========================
Statistical analysis and clustered bootstrap contrasts for E10 Mechanism Ablation.

Resamples clusters by source WAV file (so all profiles, initializations, seeds,
and variants from a sampled audio source remain together), producing:
1. `e10_success_summary.csv`: Overall success count and empirical fraction per variant.
2. `e10_contrasts.csv`: Paired contrasts between variants (delta success, 95% bootstrap CI,
   rescue, loss, net rescue).

Usage:
    python experiments/08_e10_robustness_mechanism_ablation/02_analyze_e10_ablation.py \\
        results/08_e10_robustness_mechanism_ablation/e10_run_ledger.csv \\
        --B 5000 --seed 20270920
"""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

VARIANTS = ["fgla_oracle", "fixed_1e_oracle", "online_raw", "online_env", "online_fallback", "online_full"]

CONTRASTS = [
    ("fgla_oracle", "fixed_1e_oracle"),
    ("fixed_1e_oracle", "online_raw"),
    ("online_raw", "online_env"),
    ("online_raw", "online_fallback"),
    ("online_env", "online_full"),
    ("fgla_oracle", "online_full"),
]


def analyze_e10(ledger_path: str | Path, out_dir: str | Path | None = None, B: int = 5000, seed: int = 20270920):
    ledger_path = Path(ledger_path)
    if not ledger_path.exists():
        raise FileNotFoundError(f"Run ledger not found: {ledger_path}")

    out = Path(out_dir) if out_dir else ledger_path.parent
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ledger_path)

    # 1. Pairing integrity check
    counts = df.groupby("run_key")["variant"].nunique()
    if counts.min() != counts.max() or counts.min() != len(VARIANTS):
        raise ValueError(
            f"Incomplete variant pairing! Min variants per key: {counts.min()}, "
            f"Max: {counts.max()}, Expected: {len(VARIANTS)}"
        )

    # 2. Success summary per variant
    summary = (
        df.groupby("variant")["success"]
        .agg(["count", "sum", "mean"])
        .reindex(VARIANTS)
        .reset_index()
    )
    summary.rename(columns={"count": "total_runs", "sum": "success_count", "mean": "success_rate"}, inplace=True)
    summary_path = out / "e10_success_summary.csv"
    summary.to_csv(summary_path, index=False)

    # 3. Clustered Bootstrap by source WAV file
    wide = df.pivot(index="run_key", columns="variant", values="success").astype(bool)
    meta = df.drop_duplicates("run_key").set_index("run_key")
    wide = wide.join(meta[["file"]])

    rng = np.random.default_rng(seed)
    unique_files = wide["file"].unique()
    n_files = len(unique_files)
    boot = {c: [] for c in CONTRASTS}

    print(f"Running Clustered Bootstrap (B={B}, clusters={n_files} source files)...")
    for _ in range(B):
        sampled_files = rng.choice(unique_files, size=n_files, replace=True)
        chunks = [wide[wide["file"] == f] for f in sampled_files]
        z = pd.concat(chunks, ignore_index=True)
        for c in CONTRASTS:
            boot[c].append(float(z[c[1]].mean() - z[c[0]].mean()))

    rows = []
    for A, B_var in CONTRASTS:
        rescue = float((~wide[A] & wide[B_var]).mean())
        loss = float((wide[A] & ~wide[B_var]).mean())
        delta = float(wide[B_var].mean() - wide[A].mean())
        boot_vals = np.asarray(boot[(A, B_var)])
        rows.append(
            dict(
                A=A,
                B=B_var,
                delta_success=delta,
                ci_low_95=float(np.quantile(boot_vals, 0.025)),
                ci_high_95=float(np.quantile(boot_vals, 0.975)),
                rescue_rate=rescue,
                loss_rate=loss,
                net_rescue=rescue - loss,
            )
        )

    contrasts_df = pd.DataFrame(rows)
    contrasts_path = out / "e10_contrasts.csv"
    contrasts_df.to_csv(contrasts_path, index=False)

    print("\n" + "=" * 60)
    print("E10 SUCCESS SUMMARY:")
    print("=" * 60)
    print(summary.to_string(index=False))
    print("\n" + "=" * 60)
    print("E10 PAIRED CONTRASTS (WITH 95% CLUSTERED BOOTSTRAP CI):")
    print("=" * 60)
    print(contrasts_df.to_string(index=False))
    print(f"\n[OK] Reports saved to:\n     - {summary_path}\n     - {contrasts_path}")

    return summary, contrasts_df


def main():
    parser = argparse.ArgumentParser(description="Analyze E10 Mechanism Ablation results with clustered bootstrap")
    parser.add_argument("ledger", help="Path to e10_run_ledger.csv")
    parser.add_argument("--out", default=None, help="Output directory (default: same directory as ledger)")
    parser.add_argument("--B", type=int, default=5000, help="Number of bootstrap replicates (default: 5000)")
    parser.add_argument("--seed", type=int, default=20270920, help="Random seed for bootstrap (default: 20270920)")
    args = parser.parse_args()

    analyze_e10(args.ledger, args.out, args.B, args.seed)


if __name__ == "__main__":
    main()
