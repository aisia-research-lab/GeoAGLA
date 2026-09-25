#!/usr/bin/env python3
"""04_audit_and_analyze_e10r.py
==============================
Experiment E10-R: Unified Independent Integrity Audit and Statistical Analysis.

Performs a rigorous end-to-end verification and statistical decomposition of the
locked E10-R closure experiment:
1. Hard cardinality and pairing verification (28,440 rows, 4,740 paired instances).
2. Frozen population membership audit against `e10r_locked_geometry_395.csv`.
3. Event ledger diagnostics (checkpoint rejections and fallback activations).
4. Clustered bootstrap resampling ($B = 5,000$, clustered by source audio file).
5. Generation of publication-grade tables:
   - `e10r_success_summary.csv`
   - `e10r_contrasts.csv`
   - `integrity_summary.json`
   - `E10R_AUDIT.md`

Usage:
    python experiments/08_e10_robustness_mechanism_ablation/04_audit_and_analyze_e10r.py \
        results/08_e10r_locked/e10r_run_ledger.csv \
        --out results/08_e10r_locked \
        --B 5000 --seed 20270920
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

VARIANTS = [
    "fgla_oracle",
    "fixed_1e_oracle",
    "online_raw",
    "online_env",
    "online_fallback",
    "online_full",
]

CONTRASTS = [
    ("fgla_oracle", "fixed_1e_oracle"),
    ("fixed_1e_oracle", "online_raw"),
    ("online_raw", "online_env"),
    ("online_raw", "online_fallback"),
    ("online_env", "online_full"),
    ("fgla_oracle", "online_full"),
    ("online_raw", "online_full"),
]


def audit_integrity(df: pd.DataFrame, locked_geo_path: Path) -> Dict[str, Any]:
    """Audit ledger cardinality, pairing completeness, and population membership."""
    audit_results: Dict[str, Any] = {}
    errors: List[str] = []

    # 1. Row count
    total_rows = len(df)
    expected_rows = 395 * 12 * 6
    audit_results["total_rows"] = total_rows
    audit_results["expected_rows"] = expected_rows
    if total_rows != expected_rows:
        errors.append(f"Row count mismatch: {total_rows} != {expected_rows}")

    # 2. Paired instances
    run_keys = df["run_key"].unique()
    total_instances = len(run_keys)
    expected_instances = 395 * 12
    audit_results["total_paired_instances"] = total_instances
    audit_results["expected_paired_instances"] = expected_instances
    if total_instances != expected_instances:
        errors.append(f"Paired instance count mismatch: {total_instances} != {expected_instances}")

    # 3. Duplicate checks
    dups = df.duplicated(subset=["run_key", "variant"]).sum()
    audit_results["duplicate_run_key_variant_pairs"] = int(dups)
    if dups > 0:
        errors.append(f"Found {dups} duplicate (run_key, variant) pairs")

    # 4. Six-way completeness per run_key
    counts_per_key = df.groupby("run_key")["variant"].nunique()
    incomplete_keys = (counts_per_key != 6).sum()
    audit_results["incomplete_run_keys"] = int(incomplete_keys)
    if incomplete_keys > 0:
        errors.append(f"Found {incomplete_keys} run_keys without all 6 variants")

    # 5. Population membership
    if locked_geo_path.exists():
        locked_geo = pd.read_csv(locked_geo_path)
        locked_set = set(zip(locked_geo["file"], locked_geo["profile"]))
        actual_set = set(zip(df["file"], df["profile"]))
        missing_from_actual = locked_set - actual_set
        foreign_in_actual = actual_set - locked_set

        audit_results["locked_cases_count"] = len(locked_set)
        audit_results["actual_cases_count"] = len(actual_set)
        audit_results["missing_cases"] = list(missing_from_actual)
        audit_results["foreign_cases"] = list(foreign_in_actual)

        if missing_from_actual:
            errors.append(f"{len(missing_from_actual)} locked cases missing from ledger")
        if foreign_in_actual:
            errors.append(f"{len(foreign_in_actual)} unauthorized cases present in ledger")
    else:
        errors.append(f"Locked geometry file not found: {locked_geo_path}")

    # 6. Seed mode
    if "seed_mode" in df.columns:
        modes = df["seed_mode"].unique().tolist()
        audit_results["seed_modes"] = modes
        if modes != ["historical_batch2"]:
            errors.append(f"Unexpected seed modes: {modes} (expected ['historical_batch2'])")

    audit_results["errors"] = errors
    audit_results["status"] = "PASS" if not errors else "FAIL"
    return audit_results


def compute_clustered_bootstrap(
    df: pd.DataFrame,
    B: int = 5000,
    seed: int = 20270920,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute empirical summary and clustered bootstrap paired contrasts."""
    # Empirical success summary
    summary_rows = []
    for v in VARIANTS:
        sub = df[df["variant"] == v]
        s_count = int(sub["success"].sum())
        total = len(sub)
        rate = float(s_count / total) if total > 0 else 0.0
        summary_rows.append(dict(
            variant=v,
            sum=s_count,
            count=total,
            mean=rate,
            success_pct=rate * 100.0,
        ))
    summary_df = pd.DataFrame(summary_rows)

    # Pivot table for paired analysis (indexed by run_key)
    p_succ = df.pivot(index="run_key", columns="variant", values="success")
    p_file = df.groupby("run_key")["file"].first()
    paired_df = p_succ.assign(file=p_file)

    clusters = np.sort(paired_df["file"].unique())
    n_clusters = len(clusters)
    cluster_indices = {c: paired_df.index[paired_df["file"] == c].to_numpy() for c in clusters}

    rng = np.random.default_rng(seed)

    # Pre-draw cluster resample indices
    contrast_rows = []
    for var_a, var_b in CONTRASTS:
        diff_empirical = float(paired_df[var_b].mean() - paired_df[var_a].mean()) * 100.0
        rescued = int(((paired_df[var_a] == False) & (paired_df[var_b] == True)).sum())
        lost = int(((paired_df[var_a] == True) & (paired_df[var_b] == False)).sum())
        net_rescue = rescued - lost

        # Clustered bootstrap
        boot_diffs = np.empty(B, dtype=np.float64)
        for b in range(B):
            sampled_c = rng.choice(clusters, size=n_clusters, replace=True)
            sampled_idx = np.concatenate([cluster_indices[c] for c in sampled_c])
            sub_a = paired_df.loc[sampled_idx, var_a]
            sub_b = paired_df.loc[sampled_idx, var_b]
            boot_diffs[b] = (sub_b.mean() - sub_a.mean()) * 100.0

        ci_low = float(np.percentile(boot_diffs, 2.5))
        ci_high = float(np.percentile(boot_diffs, 97.5))

        contrast_rows.append(dict(
            A=var_a,
            B=var_b,
            delta_pp=diff_empirical,
            ci_low_95=ci_low,
            ci_high_95=ci_high,
            rescues=rescued,
            losses=lost,
            net_rescue=net_rescue,
        ))

    contrasts_df = pd.DataFrame(contrast_rows)
    return summary_df, contrasts_df


def generate_audit_markdown(
    audit_res: Dict[str, Any],
    summary_df: pd.DataFrame,
    contrasts_df: pd.DataFrame,
    event_df: pd.DataFrame | None,
    out_path: Path,
) -> None:
    """Generate comprehensive academic audit markdown document."""
    lines = [
        "# E10-R Final Mechanism Attribution & Reproducibility Closure Audit",
        "",
        "- **Experiment:** E10-R Final Closure",
        f"- **Audit Status:** **{audit_res['status']}**",
        f"- **Total Rows Evaluated:** {audit_res['total_rows']:,} (Expected: {audit_res['expected_rows']:,})",
        f"- **Paired Instances:** {audit_res['total_paired_instances']:,} (Expected: {audit_res['expected_paired_instances']:,})",
        f"- **Locked Geometry Cases:** {audit_res.get('actual_cases_count', 395)} (Expected: 395)",
        "",
        "---",
        "",
        "## 1. Cardinality and Data Integrity Audit",
        "",
        "| Gate Item | Requirement | Observed Value | Status |",
        "| :--- | :--- | :---: | :---: |",
        f"| **Row Count** | Exactly 28,440 rows | {audit_res['total_rows']:,} | {'PASS' if audit_res['total_rows'] == 28440 else 'FAIL'} |",
        f"| **Paired Instances** | Exactly 4,740 instances | {audit_res['total_paired_instances']:,} | {'PASS' if audit_res['total_paired_instances'] == 4740 else 'FAIL'} |",
        f"| **Variant Completeness** | Exactly 6 variants per run_key | {6 if audit_res['incomplete_run_keys'] == 0 else 'Incomplete'} | {'PASS' if audit_res['incomplete_run_keys'] == 0 else 'FAIL'} |",
        f"| **Duplicate Key Pairs** | Exactly 0 duplicates | {audit_res['duplicate_run_key_variant_pairs']} | {'PASS' if audit_res['duplicate_run_key_variant_pairs'] == 0 else 'FAIL'} |",
        f"| **Population Conformance** | 395 locked cases only | {audit_res.get('actual_cases_count', 395)} | {'PASS' if len(audit_res.get('missing_cases', [])) == 0 and len(audit_res.get('foreign_cases', [])) == 0 else 'FAIL'} |",
        f"| **Seed Mode** | historical_batch2 | {audit_res.get('seed_modes', ['unknown'])[0]} | {'PASS' if audit_res.get('seed_modes') == ['historical_batch2'] else 'FAIL'} |",
        "",
    ]

    if audit_res["errors"]:
        lines.extend([
            "### Integrity Violations Detected:",
            "",
        ])
        for err in audit_res["errors"]:
            lines.append(f"- [FAIL] {err}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 2. Empirical Success Rate Summary",
        "",
        "| Variant | Total Runs | Success Count | Success Rate (%) |",
        "| :--- | :---: | :---: | :---: |",
    ])
    for r in summary_df.itertuples():
        lines.append(f"| `{r.variant}` | {r.count:,} | {r.sum:,} | **{r.success_pct:.2f}%** |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Clustered Bootstrap Paired Contrasts ($B=5,000$ Replicates)",
        "",
        "| Contrast (A -> B) | $\\Delta$ (pp) | 95% Clustered CI (pp) | Rescues | Losses | Net Rescue |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ])
    for r in contrasts_df.itertuples():
        lines.append(f"| `{r.A}` -> `{r.B}` | **{r.delta_pp:+.2f}** | [{r.ci_low_95:+.2f}, {r.ci_high_95:+.2f}] | {r.rescues:,} | {r.losses:,} | **{r.net_rescue:+,}** |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Event Ledger Diagnostic Summary",
        "",
    ])
    if event_df is not None and not event_df.empty:
        lines.append(f"- **Total Recorded Events:** {len(event_df):,}")
        if "fallback_used" in event_df.columns:
            fb_count = int(event_df["fallback_used"].sum())
            lines.append(f"- **Total Fallback Activations:** {fb_count:,}")
        if "candidate_accepted" in event_df.columns:
            rej_count = int((event_df["candidate_accepted"] == False).sum())
            lines.append(f"- **Total Candidate Rejections:** {rej_count:,}")
    else:
        lines.append("- Event ledger is empty (zero abnormal divergence or fallback events recorded).")

    lines.extend([
        "",
        "---",
        "",
        "## 5. Closure Sign-Off",
        "",
        f"- **Verification Status:** {'APPROVED (GREEN)' if audit_res['status'] == 'PASS' else 'REJECTED (RED)'}",
        "- **Protocol:** Locked finite-horizon recovery evaluation under Phase-2B historical parameters.",
    ])

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="E10-R Unified Audit and Analysis")
    ap.add_argument("ledger", help="Path to e10r_run_ledger.csv")
    ap.add_argument("--event-ledger", default=None, help="Path to e10r_event_ledger.csv")
    ap.add_argument("--out", default=None, help="Output directory (defaults to ledger directory)")
    ap.add_argument("--B", type=int, default=5000, help="Bootstrap replicates")
    ap.add_argument("--seed", type=int, default=20270920, help="Random seed for bootstrap")
    args = ap.parse_args()

    ledger_path = Path(args.ledger)
    if not ledger_path.exists():
        raise FileNotFoundError(f"Run ledger not found: {ledger_path}")

    out_dir = Path(args.out) if args.out else ledger_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ledger_path)
    locked_geo_path = ROOT / "experiments" / "08_e10_robustness_mechanism_ablation" / "frozen" / "e10r_locked_geometry_395.csv"

    print("Executing cardinality and integrity audit...")
    audit_res = audit_integrity(df, locked_geo_path)
    (out_dir / "integrity_summary.json").write_text(json.dumps(audit_res, indent=2), encoding="utf-8")

    print(f"Integrity status: {audit_res['status']}")
    for err in audit_res["errors"]:
        print(f"  [ERROR] {err}")

    print(f"Computing clustered bootstrap ({args.B} replicates, seed {args.seed})...")
    summary_df, contrasts_df = compute_clustered_bootstrap(df, B=args.B, seed=args.seed)

    summary_df.to_csv(out_dir / "e10r_success_summary.csv", index=False)
    contrasts_df.to_csv(out_dir / "e10r_contrasts.csv", index=False)

    event_df = None
    event_path = Path(args.event_ledger) if args.event_ledger else ledger_path.parent / "e10r_event_ledger.csv"
    if event_path.exists() and event_path.stat().st_size > 30:
        event_df = pd.read_csv(event_path)

    generate_audit_markdown(audit_res, summary_df, contrasts_df, event_df, out_dir / "E10R_AUDIT.md")
    print(f"Outputs written to: {out_dir}")


if __name__ == "__main__":
    main()
