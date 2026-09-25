#!/usr/bin/env python3
"""05_analyze_e10r2.py
======================
Experiment E10-R2: Clustered Bootstrap Statistical Analysis & Independent Audit.
Complies strictly with Section 16, 17, 18, 19, 31, 32 of E10-R2 Final Freeze Guide:
1. Hard Cardinality & Integrity Gates (395 cases, 4,740 pairs, 28,440 rows).
2. Variant Success Rates (e10r2_success_summary.csv).
3. Pre-specified contrasts + Exploratory interaction contrast (e10r2_contrasts.csv).
4. Clustered Bootstrap by source WAV file (B=5,000, seed=20270920).
5. Paired Rescue & Loss analysis (counts and percentages).
6. Generates E10R2_INTEGRITY_AUDIT.md and integrity_summary.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

VARIANTS = [
    "fgla_oracle",
    "fixed_1e_oracle",
    "online_raw",
    "online_env",
    "online_fallback",
    "online_full",
]

PRE_SPECIFIED_CONTRASTS = [
    ("fgla_oracle", "fixed_1e_oracle", "pre-specified: minimax gain"),
    ("fixed_1e_oracle", "online_raw", "pre-specified: online adaptation gain"),
    ("online_raw", "online_env", "pre-specified: stability envelope effect"),
    ("online_raw", "online_fallback", "pre-specified: fallback effect"),
    ("online_env", "online_full", "pre-specified: fallback on enveloped policy"),
    ("fgla_oracle", "online_full", "pre-specified: headline canonical gain"),
    ("online_raw", "online_full", "exploratory interaction contrast"),
]


def audit_and_analyze_e10r2(
    ledger_path: str | Path,
    out_dir: str | Path | None = None,
    B: int = 5000,
    seed: int = 20270920,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    ledger_path = Path(ledger_path)
    if not ledger_path.exists():
        raise FileNotFoundError(f"Run ledger not found: {ledger_path}")

    base_out = Path(out_dir) if out_dir else ledger_path.parent
    res_dir = base_out if base_out.name == "results" else base_out / "results"
    audit_dir = base_out / "audit" if base_out.name != "results" else base_out.parent / "audit"
    res_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ledger_path)

    # 1. HARD CARDINALITY GATES (Section 16)
    total_rows = len(df)
    n_keys = df["run_key"].nunique()
    variants_per_key = df.groupby("run_key")["variant"].nunique()
    min_v = int(variants_per_key.min()) if not variants_per_key.empty else 0
    max_v = int(variants_per_key.max()) if not variants_per_key.empty else 0
    duplicates = int(df.duplicated(subset=["run_key", "variant"]).sum())
    unique_cases = df.groupby(["file", "profile"]).ngroups

    gate_row_count = total_rows == 28440
    gate_instances = n_keys == 4740
    gate_variants = (min_v == 6) and (max_v == 6)
    gate_duplicates = duplicates == 0
    gate_cases = unique_cases == 395

    all_gates_pass = (
        gate_row_count and gate_instances and gate_variants and gate_duplicates and gate_cases
    )

    integrity_dict = {
        "status": "PASS" if all_gates_pass else "NO-GO",
        "total_rows": total_rows,
        "total_paired_instances": n_keys,
        "locked_geometry_cases": unique_cases,
        "variants_per_key_min": min_v,
        "variants_per_key_max": max_v,
        "duplicate_count": duplicates,
        "gates": {
            "cardinality_28440": bool(gate_row_count),
            "paired_instances_4740": bool(gate_instances),
            "variant_completeness_6": bool(gate_variants),
            "zero_duplicates": bool(gate_duplicates),
            "locked_cases_395": bool(gate_cases),
        },
        "errors": [],
    }

    if not all_gates_pass:
        integrity_dict["errors"].append(
            f"Hard Cardinality Failure: rows={total_rows}/28440, keys={n_keys}/4740, "
            f"cases={unique_cases}/395, variants={min_v}-{max_v}/6, dups={duplicates}"
        )

    # Save integrity summary json
    (audit_dir / "integrity_summary.json").write_text(
        json.dumps(integrity_dict, indent=2), encoding="utf-8"
    )

    # 2. SUCCESS SUMMARY PER VARIANT (Section 17)
    summary = (
        df.groupby("variant")["success"]
        .agg(["count", "sum", "mean"])
        .reindex(VARIANTS)
        .reset_index()
    )
    summary.rename(
        columns={"count": "total_runs", "sum": "success_count", "mean": "success_rate"},
        inplace=True,
    )
    summary["success_pct"] = summary["success_rate"] * 100.0
    summary_path = res_dir / "e10r2_success_summary.csv"
    summary.to_csv(summary_path, index=False)

    # 3. CLUSTERED BOOTSTRAP BY SOURCE WAV FILE (Section 18, 19)
    wide = df.pivot(index="run_key", columns="variant", values="success").astype(bool)
    meta = df.drop_duplicates("run_key").set_index("run_key")
    wide = wide.join(meta[["file"]])

    rng = np.random.default_rng(seed)
    unique_files = wide["file"].unique()
    n_files = len(unique_files)
    boot = {f"{c[0]}->{c[1]}": [] for c in PRE_SPECIFIED_CONTRASTS}

    print(f"Running Clustered Bootstrap (B={B}, clusters={n_files} source files, seed={seed})...")
    for _ in range(B):
        sampled_files = rng.choice(unique_files, size=n_files, replace=True)
        chunks = [wide[wide["file"] == f] for f in sampled_files]
        z = pd.concat(chunks, ignore_index=True)
        for A, B_var, _label in PRE_SPECIFIED_CONTRASTS:
            k = f"{A}->{B_var}"
            boot[k].append(float(z[B_var].mean() - z[A].mean()))

    rows = []
    n_pairs = len(wide)
    for A, B_var, label in PRE_SPECIFIED_CONTRASTS:
        k = f"{A}->{B_var}"
        rescue_mask = ~wide[A] & wide[B_var]
        loss_mask = wide[A] & ~wide[B_var]
        rescue_count = int(rescue_mask.sum())
        loss_count = int(loss_mask.sum())
        net_rescue_count = rescue_count - loss_count
        rescue_rate = float(rescue_mask.mean())
        loss_rate = float(loss_mask.mean())
        net_rescue_rate = rescue_rate - loss_rate
        delta = float(wide[B_var].mean() - wide[A].mean())
        boot_vals = np.asarray(boot[k])

        rows.append(
            dict(
                A=A,
                B=B_var,
                label=label,
                delta_pp=delta * 100.0,
                ci_low_95=float(np.quantile(boot_vals, 0.025)) * 100.0,
                ci_high_95=float(np.quantile(boot_vals, 0.975)) * 100.0,
                rescues=rescue_count,
                rescue_pct=rescue_rate * 100.0,
                losses=loss_count,
                loss_pct=loss_rate * 100.0,
                net_rescue=net_rescue_count,
                net_rescue_pct=net_rescue_rate * 100.0,
            )
        )

    contrasts_df = pd.DataFrame(rows)
    contrasts_path = res_dir / "e10r2_contrasts.csv"
    contrasts_df.to_csv(contrasts_path, index=False)

    # 4. GENERATE E10R2_INTEGRITY_AUDIT.md
    audit_md_path = audit_dir / "E10R2_INTEGRITY_AUDIT.md"
    md_content = f"""# E10-R2 Final Scientific Integrity & Cardinality Audit

- **Experiment:** E10-R2 Canonical-Equivalence Repair & Final Freeze
- **Audit Status:** **{'GREEN (PASS)' if all_gates_pass else 'NO-GO (FAIL)'}**
- **Clustered Bootstrap Seed:** `{seed}` (B={B:,} replicates clustered by audio source file)
- **Success Criteria:** `final_orbit_error <= 0.10 * initial_orbit_error` AND `final_magnitude_residual <= 1e-5`

---

## 1. Cardinality and Data Integrity Audit

| Gate Item | Requirement | Observed Value | Status |
| :--- | :--- | :---: | :---: |
| **Row Count** | Exactly 28,440 rows | {total_rows:,} | {'PASS' if gate_row_count else 'FAIL'} |
| **Paired Instances** | Exactly 4,740 instances | {n_keys:,} | {'PASS' if gate_instances else 'FAIL'} |
| **Locked Geometry Cases** | Exactly 395 cases | {unique_cases} | {'PASS' if gate_cases else 'FAIL'} |
| **Variant Completeness** | Exactly 6 variants per run_key | {min_v} - {max_v} | {'PASS' if gate_variants else 'FAIL'} |
| **Duplicate Key Pairs** | Exactly 0 duplicates | {duplicates} | {'PASS' if gate_duplicates else 'FAIL'} |

---

## 2. Empirical Success Rate Summary

| Variant | Total Runs | Success Count | Success Rate (%) |
| :--- | :---: | :---: | :---: |
"""
    for _, r in summary.iterrows():
        md_content += f"| `{r['variant']}` | {int(r['total_runs']):,} | {int(r['success_count']):,} | **{r['success_pct']:.2f}%** |\n"

    md_content += """
---

## 3. Pre-specified Contrasts & Clustered Bootstrap (B=5,000)

| Contrast (A -> B) | Label | Delta (pp) | 95% Clustered CI | Rescues | Losses | Net Rescue |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
"""
    for _, r in contrasts_df.iterrows():
        md_content += (
            f"| `{r['A']}` -> `{r['B']}` | {r['label']} | "
            f"**{r['delta_pp']:+.2f}** | [{r['ci_low_95']:+.2f}, {r['ci_high_95']:+.2f}] | "
            f"{int(r['rescues']):,} ({r['rescue_pct']:.2f}%) | "
            f"{int(r['losses']):,} ({r['loss_pct']:.2f}%) | "
            f"**{int(r['net_rescue']):+,}** ({r['net_rescue_pct']:+.2f}%) |\n"
        )

    md_content += "\n---\n*Generated automatically by 05_analyze_e10r2.py*\n"
    audit_md_path.write_text(md_content, encoding="utf-8")

    print("\n" + "=" * 60)
    print("E10-R2 EMPIRICAL SUCCESS SUMMARY:")
    print("=" * 60)
    print(summary.to_string(index=False))
    print("\n" + "=" * 60)
    print("E10-R2 PAIRED CONTRASTS (WITH 95% CLUSTERED BOOTSTRAP CI):")
    print("=" * 60)
    print(contrasts_df.to_string(index=False))
    print(f"\n[OK] Reports saved to:\n     - {summary_path}\n     - {contrasts_path}\n     - {audit_md_path}")

    return summary, contrasts_df, integrity_dict


def main():
    parser = argparse.ArgumentParser(description="Audit and Analyze E10-R2 canonical results")
    parser.add_argument("ledger", help="Path to e10r2_run_ledger.csv")
    parser.add_argument("--out", default=None, help="Output directory")
    parser.add_argument("--B", type=int, default=5000, help="Number of bootstrap replicates")
    parser.add_argument("--seed", type=int, default=20270920, help="Random seed for bootstrap")
    args = parser.parse_args()

    audit_and_analyze_e10r2(args.ledger, args.out, args.B, args.seed)


if __name__ == "__main__":
    main()
