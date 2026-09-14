#!/usr/bin/env python3
"""Validation audit of canonical E6 and held-out ledgers.
Section 4 & Gate A of ICLR 2027 Next Experiment Handoff for Students A & B.
"""
from __future__ import annotations

import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root / 'src') not in sys.path:
    sys.path.insert(0, str(_repo_root / 'src'))

import argparse
import math
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common import read_csv, dump_json, fnum

ROOT = Path(__file__).resolve().parents[1]


def audit_ledger(ledger_rows: list[dict], name: str = "canonical") -> list[dict]:
    issues = []
    ids = []
    
    for i, r in enumerate(ledger_rows):
        cid = r.get("case_id") or f"row_{i}"
        ids.append(cid)
        
        lm = fnum(r.get("lambda_minus"))
        lp = fnum(r.get("lambda_plus"))
        
        # 1. Spectrum check
        if lm is None or lp is None:
            issues.append({"ledger": name, "case": cid, "issue": "missing_spectrum"})
        elif not (-1e-10 <= lm <= lp <= 1.0 + 1e-10):
            issues.append({
                "ledger": name, "case": cid, "issue": "illegal_spectrum",
                "lambda_minus": lm, "lambda_plus": lp
            })
            
        # 2. Predicted rate finite and valid
        qg = fnum(r.get("q_gla_pred"))
        qf = fnum(r.get("q_fgla_pred"))
        qo = fnum(r.get("q_oracle_pred"))
        
        for k, v in [("q_gla_pred", qg), ("q_fgla_pred", qf), ("q_oracle_pred", qo)]:
            if v is None or not math.isfinite(v):
                issues.append({"ledger": name, "case": cid, "issue": f"invalid_{k}", "val": v})
            elif not (-1e-6 <= v <= 1.0 + 1e-6):
                issues.append({"ledger": name, "case": cid, "issue": f"out_of_bounds_{k}", "val": v})
                
        # 3. Predicted ordering: qo <= qf <= qg (with 1e-8 numerical tolerance)
        if None not in (qg, qf, qo):
            if qo > qf + 1e-8 or qf > qg + 1e-8:
                issues.append({
                    "ledger": name, "case": cid, "issue": "predicted_ordering_fail",
                    "qo": qo, "qf": qf, "qg": qg
                })
                
        # 4. Observed rates finite
        for k in ["q_gla_obs", "q_fgla_obs", "q_oracle_obs"]:
            v = fnum(r.get(k))
            if v is not None and not math.isfinite(v):
                issues.append({"ledger": name, "case": cid, "issue": f"nonfinite_{k}", "val": v})

    # 5. Duplicate ID check
    for cid in set(ids):
        if ids.count(cid) > 1:
            issues.append({"ledger": name, "case": cid, "issue": "duplicate_case_id", "count": ids.count(cid)})

    return issues


def run_validation(canonical_path: str | Path, heldout_path: str | Path | None, out_dir: str | Path):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    
    canonical_file = Path(canonical_path)
    if not canonical_file.exists():
        raise FileNotFoundError(f"Canonical ledger not found: {canonical_file}")
    
    can_rows = read_csv(canonical_file)
    issues = audit_ledger(can_rows, name="canonical_e6")
    
    heldout_rows = []
    if heldout_path and Path(heldout_path).exists():
        heldout_rows = read_csv(Path(heldout_path))
        heldout_issues = audit_ledger(heldout_rows, name="heldout_e6")
        issues.extend(heldout_issues)
        
    report = {
        "schema_version": 1,
        "n_canonical_cases": len(can_rows),
        "n_heldout_cases": len(heldout_rows),
        "total_cases_audited": len(can_rows) + len(heldout_rows),
        "n_issues": len(issues),
        "pass": len(issues) == 0,
        "issues": issues,
    }
    
    out_file = out / "integrity_report.json"
    dump_json(report, out_file)
    
    print(f"Validation Audit: PASS={report['pass']} (Issues: {report['n_issues']}, Canonical: {len(can_rows)}, Held-out: {len(heldout_rows)})")
    return report


def main():
    parser = argparse.ArgumentParser(description="Scientific validation audit of E6 ledgers")
    parser.add_argument("--canonical", default=str(ROOT / "results" / "e6_geometry_opportunity" / "e6_case_ledger.csv"))
    parser.add_argument("--heldout", default=str(ROOT / "results" / "e6_geometry_opportunity" / "e6_heldout_ledger.csv"))
    parser.add_argument("--out", default=str(ROOT / "results" / "e6_geometry_opportunity"))
    args = parser.parse_args()

    heldout_p = args.heldout if Path(args.heldout).exists() else None
    run_validation(args.canonical, heldout_p, args.out)


if __name__ == "__main__":
    main()