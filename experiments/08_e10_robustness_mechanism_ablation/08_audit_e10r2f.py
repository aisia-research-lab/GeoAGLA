#!/usr/bin/env python3
"""Independent mechanical audit for E10-R2F outputs."""
from pathlib import Path
import argparse, json, pandas as pd
ap=argparse.ArgumentParser(); ap.add_argument("--closure-dir",required=True); a=ap.parse_args()
d=Path(a.closure_dir)
eq=pd.read_csv(d/"tests/trajectory_equivalence_report.csv")
nl=pd.read_csv(d/"tests/no_oracle_leakage_report.csv")
ev=pd.read_csv(d/"events/e10r2_complete_event_ledger.csv")
rr=pd.read_csv(d/"forensic_rerun/e10r2f_online_event_rerun_ledger.csv")
rp=pd.read_csv(d/"forensic_rerun/rerun_primary_equivalence.csv")
checks={
 "equivalence_rows_at_least_18":len(eq)>=18,
 "all_equivalence_pass":(eq.status=="PASS").all(),
 "no_oracle_leakage_pass":(nl.status=="PASS").all(),
 "online_rerun_rows_18960":len(rr)==18960,
 "event_rows_834240":len(ev)==834240,
 "event_duplicates_zero":not ev.duplicated(["run_key","variant","block_index"]).any(),
 "events_per_run_exact_44":bool((ev.groupby(["run_key","variant"]).size()==44).all()),
 "rerun_primary_equivalence_pass":(rp.status=="PASS").all(),
}
if "fallback_used" in ev:
    checks["raw_no_fallback"]=not ev.loc[ev.variant=="online_raw","fallback_used"].astype(bool).any()
    checks["env_no_fallback"]=not ev.loc[ev.variant=="online_env","fallback_used"].astype(bool).any()
status="PASS" if all(checks.values()) else "FAIL"
(d/"audit").mkdir(exist_ok=True)
(d/"audit/E10R2F_MECHANICAL_AUDIT.json").write_text(json.dumps({"checks":checks,"status":status},indent=2))
print(json.dumps({"checks":checks,"status":status},indent=2))
raise SystemExit(0 if status=="PASS" else 2)
