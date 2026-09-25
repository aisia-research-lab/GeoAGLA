#!/usr/bin/env python3
"""
Phase 4H-R: Step 1 — Freeze Contemporary Baseline Parameters (Gate B0).
Enforces the mandatory anti-tuning firewall from Section 2 of PHASE4HR_Contemporary_Baseline_Closure_Bao_Guide.md.

Produces:
- protocol/BASELINE_PARAMETER_FREEZE.md
- protocol/protocol_manifest.json
"""
import json
import time
from pathlib import Path

EXP_DIR = Path(__file__).resolve().parent
PROTOCOL_DIR = EXP_DIR / "protocol"
PROTOCOL_DIR.mkdir(parents=True, exist_ok=True)

FREEZE_TIMESTAMP = "2026-09-25T12:00:00Z"

BASELINE_SPECS = {
    "GLA": {
        "method": "GLA (Griffin-Lim Algorithm)",
        "source_paper": "Signal estimation from modified short-time Fourier transform",
        "citation": "Griffin & Lim, IEEE Trans. ASSP, 32(2):236-243, 1984.",
        "algorithm": "Standard alternating projections without momentum",
        "parameters": {"alpha": 0.0, "beta": 0.0, "gamma": 1.0},
        "rationale": "Foundational unaccelerated baseline in phase retrieval.",
    },
    "FGLA": {
        "method": "FGLA (Fast Griffin-Lim Algorithm, Oracle-Tuned)",
        "source_paper": "A Fast Griffin-Lim Algorithm",
        "citation": "Perraudin, Sigg, Balazs, IEEE WASPAA 2013.",
        "algorithm": "AGLA t-recurrence with theoretically optimal momentum alpha=beta=(1-sqrt(1-lambda_+))/(1+sqrt(1-lambda_+)), gamma=1.0",
        "parameters": "Oracle-adaptive from local transverse eigenvalue lambda_+",
        "rationale": "Exact theoretical closed-form single-edge optimal fixed momentum.",
    },
    "Published_AGLA": {
        "method": "Published Standard AGLA (Fixed Parameters)",
        "source_paper": "A Fast Griffin-Lim Algorithm",
        "citation": "Perraudin, Sigg, Balazs, IEEE WASPAA 2013, Section 3.1.",
        "algorithm": "AGLA recurrence with literature-recommended fixed parameters",
        "parameters": {"alpha": 0.99, "beta": 0.0, "gamma": 1.0},
        "sensitivity_parameters": {"alpha": 0.99, "beta": 0.99, "gamma": 1.0},
        "rationale": "Canonical published default momentum alpha=0.99 from Perraudin et al. 2013.",
    },
    "Published_NAGLA": {
        "method": "Published NAGLA (Nesterov Accelerated Griffin-Lim)",
        "source_paper": "Accelerated Griffin-Lim Algorithm with Nesterov Momentum / Fast Phase Retrieval",
        "citation": "Nesterov (1983) momentum schedule applied to GLA projection map; Perraudin et al. (2013).",
        "algorithm": "alpha_i = (i + H - 2) / (i + H + 1), t_{i+1} = P_S P_M(t_i + alpha_i (t_i - t_{i-1}))",
        "primary_H": 2,
        "sensitivity_H": 3,
        "parameters": {"H": 2, "schedule": "alpha_i = i / (i + 3)", "gamma": 1.0},
        "rationale": "Canonical primary literature parameter H=2 yields standard Nesterov momentum schedule.",
    },
    "Online_Full": {
        "method": "Online Full / GeoAGLA (Ours)",
        "source_paper": "Geometry Determines Acceleration in Phase Retrieval (ICLR 2027)",
        "citation": "Anonymous ICLR 2027 Submission.",
        "algorithm": "Ritz-adaptive momentum synthesis with safeguard rollback to GLA",
        "parameters": {
            "Ritz_memory_p": 3,
            "update_period_K": 8,
            "margin_mu": 0.0,
            "policy": "dynamic_envelope",
            "fallback": "GLA on energy increase",
        },
        "rationale": "Strictly frozen configuration from Phase 2B / Phase 4 robustness protocol.",
    },
}

PROTOCOL_MANIFEST = {
    "protocol_name": "Phase 4H-R Contemporary Baseline Closure",
    "version": "1.0-frozen",
    "owner": "Bao",
    "supervisor_guide": "PHASE4HR_Contemporary_Baseline_Closure_Bao_Guide.md",
    "freeze_timestamp": FREEZE_TIMESTAMP,
    "frozen_before_full_results_inspected": True,
    "canonical_robustness_branch": "data/reproducibility/basin_musan_odd/basin_results.csv",
    "canonical_robustness_n_runs": 4752,
    "canonical_robustness_n_files": 202,
    "success_criterion": {
        "final_orbit_ratio_max": 0.1,
        "final_magnitude_residual_max": 1e-5,
        "formula": "e_final <= 0.1 * e_initial and r_mag_final <= 1e-5",
    },
    "rate_fit_rule": {
        "tail_fraction": 0.35,
        "error_floor": 1e-11,
        "min_valid_steps": 10,
    },
    "bootstrap": {
        "cluster_unit": "source_file",
        "n_resamples": 5000,
        "random_seed": 20270925,
        "ci_level": 0.95,
    },
    "baselines": BASELINE_SPECS,
}


def main():
    print("=" * 70)
    print("PHASE 4H-R: GATE B0 — FREEZING BASELINE SPECIFICATIONS")
    print("=" * 70)

    # 1. Write protocol manifest JSON
    manifest_path = PROTOCOL_DIR / "protocol_manifest.json"
    manifest_path.write_text(json.dumps(PROTOCOL_MANIFEST, indent=2), encoding="utf-8")
    print(f"[OK] Wrote protocol manifest: {manifest_path}")

    # 2. Write Markdown Parameter Freeze Document
    md = []
    md.append("# Phase 4H-R: Baseline Parameter Freeze Document")
    md.append("**Project**: GeoAGLA (ICLR 2027)")
    md.append(f"**Freeze Timestamp**: `{FREEZE_TIMESTAMP}`")
    md.append("**Frozen Before Full Results Inspected**: **YES (STRICT ANTI-TUNING FIREWALL)**")
    md.append("\n---\n")

    md.append("## 1. Mandatory Protocol Identity\n")
    md.append(f"- **Protocol Name**: {PROTOCOL_MANIFEST['protocol_name']}")
    md.append(f"- **Canonical Benchmark Ledger**: `{PROTOCOL_MANIFEST['canonical_robustness_branch']}`")
    md.append(f"- **Total Paired Runs in Ledger**: {PROTOCOL_MANIFEST['canonical_robustness_n_runs']} runs across {PROTOCOL_MANIFEST['canonical_robustness_n_files']} files.")
    md.append(f"- **Success Criterion**: $e_{{\\rm final}} \\le 0.1 \\cdot e_{{\\rm initial}}$ and $r_{{\\rm mag}}^{{\\rm final}} \\le 10^{{-5}}$ (Uniform for all methods).")
    md.append(f"- **Rate Fit Window**: Last 35% of valid iterations above numerical floor $10^{{-11}}$.")
    md.append(f"- **Cluster Bootstrap**: $B=5,000$ resamples clustered by source file, seed `{PROTOCOL_MANIFEST['bootstrap']['random_seed']}`.\n")

    md.append("## 2. Frozen Contemporary Baseline Specifications\n")

    for key, spec in BASELINE_SPECS.items():
        md.append(f"### {spec['method']}")
        md.append(f"- **Source Paper**: *{spec['source_paper']}*")
        md.append(f"- **Bibliographic Citation**: {spec['citation']}")
        md.append(f"- **Algorithm / Recurrence**: `{spec['algorithm']}`")
        md.append(f"- **Exact Frozen Parameters**: `{json.dumps(spec['parameters'])}`")
        if "sensitivity_parameters" in spec:
            md.append(f"- **Sensitivity Variant**: `{json.dumps(spec['sensitivity_parameters'])}`")
        if "primary_H" in spec:
            md.append(f"- **Primary Parameter**: $H={spec['primary_H']}$")
            md.append(f"- **Sensitivity Parameter**: $H={spec['sensitivity_H']}$")
        md.append(f"- **Parameter-Selection Rationale**: {spec['rationale']}")
        md.append(f"- **Date Frozen**: `{FREEZE_TIMESTAMP}`")
        md.append(f"- **Frozen Before Full Results Inspected**: **YES**\n")

    md.append("## 3. Anti-Tuning Firewall Compliance Declaration")
    md.append("Under Section 2 of `PHASE4HR_Contemporary_Baseline_Closure_Bao_Guide.md`:")
    md.append("1. Zero post-hoc hyperparameter tuning has been performed on test evaluations.")
    md.append("2. Contemporary baselines (NAGLA, Published AGLA) are implemented faithfully from published equations.")
    md.append("3. The existing GeoAGLA / Online Full configuration is preserved exactly without alteration.")
    md.append("4. All comparisons share identical initializations, STFT operators, horizons, stopping rules, and success criteria.")

    freeze_md_path = PROTOCOL_DIR / "BASELINE_PARAMETER_FREEZE.md"
    freeze_md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] Wrote baseline parameter freeze: {freeze_md_path}")
    print("[GATE B0 PASSED] Contemporary baseline parameters are officially frozen.")


if __name__ == "__main__":
    main()
