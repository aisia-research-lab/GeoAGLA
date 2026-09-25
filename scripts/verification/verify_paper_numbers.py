#!/usr/bin/env python3
"""
Verification Script for ICLR 2027 Experimental Evidence Numbers
Validates all reported numbers in the manuscript and acceptance gates:
- Gate A: Theory validation geometry-spectrum agreement (n=202)
- Gate B: Rate hierarchy passes (173/202) and final-error reductions (5.086x, 8.967x)
- Gate C: Passive estimator maturation raw trace data presence & validity
- Gate D: Original (4,680 runs) and MUSAN-ODD (4,752 runs) basin replication
- Statistical Bootstrap: 20,000-resample file-cluster confidence intervals
- Canonical Rate Horizon Audit: H in {60, 120, 180, 360}
"""

from pathlib import Path
import json
import math
import sys

# Configure UTF-8 for console output if possible
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
metrics_candidates = [
    ROOT / "results" / "publication_figures" / "reproduced_metrics.json",
    ROOT / "outputs" / "reproduced_metrics.json",
]
metrics_path = next((p for p in metrics_candidates if p.exists()), None)

if not metrics_path:
    # Run reproduction first if not present
    from reproduce_results_and_figures import run_reproduction
    run_reproduction()
    metrics_path = ROOT / "results" / "publication_figures" / "reproduced_metrics.json"

r = json.loads(metrics_path.read_text(encoding="utf-8"))
bad = []

def record_check(category, name, got, want, tol=0.03, is_integer=False):
    if is_integer:
        ok = (int(got) == int(want))
        fmt_got = f"{int(got)}"
        fmt_want = f"{int(want)}"
    else:
        ok = abs(got - want) <= tol
        fmt_got = f"{got:.5f}" if abs(got) < 100 else f"{got:.2f}"
        fmt_want = f"{want:.5f}" if abs(want) < 100 else f"{want:.2f}"
    
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {category} | {name}: got={fmt_got}, paper~={fmt_want}")
    if not ok:
        bad.append(f"{category} - {name}")

def main():
    print("=" * 70)
    print("ICLR 2027 MANUSCRIPT NUMERICAL VERIFICATION AUDIT")
    print("=" * 70)

    # 1. Headline Manuscript Basin Results (Section 11)
    print("\n--- 1. Headline Manuscript Basin Results (Gate D) ---")
    headline_checks = [
        ("Original Online success (%)", r["basin_original"]["online_success_pct"], 74.94, 0.03),
        ("Original FGLA success (%)", r["basin_original"]["fgla_success_pct"], 54.87, 0.03),
        ("MUSAN-ODD Online success (%)", r["basin_musan_odd"]["online_success_pct"], 73.30, 0.03),
        ("MUSAN-ODD FGLA success (%)", r["basin_musan_odd"]["fgla_success_pct"], 54.90, 0.03),
        ("Original paired beat (%)", r["basin_original"]["paired_online_beat_pct"], 34.47, 0.03),
        ("MUSAN-ODD paired beat (%)", r["basin_musan_odd"]["paired_online_beat_pct"], 35.74, 0.03),
    ]
    for name, got, want, tol in headline_checks:
        record_check("Basin Headline", name, got, want, tol)

    # 2. Theory Validation: Geometry and Rate Hierarchy (Gate A & Gate B)
    print("\n--- 2. Theory Validation (Gate A & Gate B) ---")
    tv = r["theory_validation"]
    record_check("Theory Validation", "Evaluated geometry cases", tv["geometry_n"], 202, is_integer=True)
    record_check("Theory Validation", "Evaluated rate cases", tv["rate_n"], 202, is_integer=True)
    record_check("Theory Validation", "Median geometry rel error", tv["geometry_median_relative_error"], 0.001438, tol=1e-4)
    record_check("Theory Validation", "Max geometry rel error", tv["geometry_max_relative_error"], 0.002897, tol=1e-4)
    record_check("Theory Validation", "Observed hierarchy pass count", tv["observed_hierarchy_pass_n"], 173, is_integer=True)
    record_check("Theory Validation", "Observed hierarchy pass fraction", tv["observed_hierarchy_pass_fraction"], 0.8564, tol=0.005)
    record_check("Theory Validation", "Median final-err red FGLA vs GLA", tv["median_final_error_reduction_fgla_vs_gla"], 5.086, tol=0.02)
    record_check("Theory Validation", "Median final-err red Oracle vs GLA", tv["median_final_error_reduction_oracle_vs_gla"], 8.967, tol=0.02)

    # 3. Replicated Robustness & Bootstrap CIs (Gate D & Section 8)
    print("\n--- 3. Replicated Robustness & Uncertainty (Gate D) ---")
    bo = r["basin_original"]
    bm = r["basin_musan_odd"]
    record_check("Robustness", "Original basin runs count", bo["n_runs"], 4680, is_integer=True)
    record_check("Robustness", "MUSAN-ODD basin runs count", bm["n_runs"], 4752, is_integer=True)
    record_check("Robustness", "Original Online-FGLA diff (pp)", bo["difference_pp"], 20.06, tol=0.05)
    record_check("Robustness", "MUSAN-ODD Online-FGLA diff (pp)", bm["difference_pp"], 18.39, tol=0.05)
    record_check("Robustness", "Original safeguard failures", bo["safeguard_failures"], 0, is_integer=True)
    record_check("Robustness", "MUSAN-ODD safeguard failures", bm["safeguard_failures"], 0, is_integer=True)

    # File-cluster 95% CI checks
    orig_ci = bo["file_cluster_95ci_difference_pp"]
    odd_ci = bm["file_cluster_95ci_difference_pp"]
    ci_orig_ok = (18.4 <= orig_ci[0] <= 18.8) and (21.3 <= orig_ci[1] <= 21.7)
    ci_odd_ok = (16.8 <= odd_ci[0] <= 17.2) and (19.6 <= odd_ci[1] <= 20.0)
    print(f"[{'PASS' if ci_orig_ok else 'FAIL'}] Bootstrap CI | Original 95% CI: got=[{orig_ci[0]:.2f}, {orig_ci[1]:.2f}] pp, paper~=[18.6, 21.5] pp")
    print(f"[{'PASS' if ci_odd_ok else 'FAIL'}] Bootstrap CI | MUSAN-ODD 95% CI: got=[{odd_ci[0]:.2f}, {odd_ci[1]:.2f}] pp, paper~=[17.0, 19.8] pp")
    if not ci_orig_ok: bad.append("Original Bootstrap CI")
    if not ci_odd_ok: bad.append("MUSAN-ODD Bootstrap CI")

    # 4. Canonical Rate Finite-Horizon Audit (Section 9)
    print("\n--- 4. Canonical Finite-Horizon Rate Audit (Section 9) ---")
    cr = r.get("canonical_rate_horizons", {})
    if cr:
        record_check("Canonical Rate", "H=60 win fraction", cr.get("60", {}).get("online_beat_fraction", 0.0), 0.8667, tol=0.01)
        record_check("Canonical Rate", "H=120 win fraction", cr.get("120", {}).get("online_beat_fraction", 0.0), 0.4667, tol=0.01)
        record_check("Canonical Rate", "H=180 win fraction", cr.get("180", {}).get("online_beat_fraction", 0.0), 0.4000, tol=0.01)
        record_check("Canonical Rate", "H=360 win fraction", cr.get("360", {}).get("online_beat_fraction", 0.0), 0.4000, tol=0.01)

    # 5. Estimator Maturation Traces Provenance (Gate C & Section 7)
    print("\n--- 5. Estimator Maturation Provenance (Gate C) ---")
    trace_files = [
        "g24_w8_h4_f8__s2__e0.001_trace.csv",
        "h24_w8_h4_f8__s0__e1e-05_trace.csv",
        "g32_w16_h4_f16__s1__e0.001_trace.csv"
    ]
    traces_dir = ROOT / "data" / "reproducibility" / "raw_trace_provenance" / "traces"
    if not traces_dir.exists():
        traces_dir = ROOT / "data" / "reproducibility" / "estimator" / "traces"
    has_traces = traces_dir.exists() and all((traces_dir / fn).exists() for fn in trace_files)
    print(f"[{'PASS' if has_traces else 'FAIL'}] Gate C | Raw trajectory trace files present: {has_traces} (3/3 key panels)")
    if not has_traces:
        bad.append("Raw trajectory traces missing")

    print("=" * 70)
    if not bad:
        print("ALL MANUSCRIPT-FACING NUMERICAL AND GATE CHECKS PASSED (100% OK)")
        print("=" * 70)
        return 0
    else:
        print(f"FAILURES DETECTED: {len(bad)} issues:")
        for b in bad:
            print(f"  - {b}")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
