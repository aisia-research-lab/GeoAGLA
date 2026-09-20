#!/usr/bin/env python3
"""
adapt_phase1er_horizon.py
==========================
Cau noi (adapter) chuyen `results/phase1er/failure_decomposition.json` (dang
raw per-case cua Phase-1E-R) thanh dinh dang RAW-per-run ma
`build_e6_ledger.py` / `analyze_horizons.py` (goi geometry_accel_next_experiments_v1)
mong doi:

    {"rows": [{"config":..., "seed":..., "epsilon":..., "n_iter":...,
                "q_online":..., "q_fgla":..., "beats":...,
                "final_edge_rel_error":...}, ...]}

KHONG dong bang lai bat ky tham so khoa hoc nao -- chi doi ten truong va
tiem gia tri `n_iter` co dinh (horizon da dong bang cua Phase-1E-R, truyen
qua --horizon-value, PHAI khop voi horizon thuc te ma repaired policy da
chay, khong duoc tu chon de "khop dep" voi ket qua mong muon).

Cach dung:
    python adapt_phase1er_horizon.py \\
        --failure-decomposition results/phase1er/failure_decomposition.json \\
        --horizon-value 360 \\
        --out results/phase1er/horizon_audit_raw_for_e6.json
"""
import argparse
import json
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--failure-decomposition", required=True)
    ap.add_argument(
        "--horizon-value", type=int, required=True,
        help="Horizon co dinh (vong lap) ma repaired dynamic_envelope policy "
             "da chay de sinh ra failure_decomposition.json nay. Phai khop "
             "dung horizon thuc te da dong bang -- khong tu chon.",
    )
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    src = json.loads(Path(args.failure_decomposition).read_text())
    if not isinstance(src, list):
        raise ValueError(
            f"Ky vong {args.failure_decomposition} la 1 list cac case -- "
            f"nhung nhan duoc {type(src)}. Kiem tra lai file dau vao."
        )

    rows = []
    missing_fields = set()
    for r in src:
        required = ["config", "seed", "epsilon", "q_online", "q_fgla"]
        for k in required:
            if k not in r:
                missing_fields.add(k)
        rows.append({
            "config": r.get("config"),
            "seed": r.get("seed"),
            "epsilon": r.get("epsilon"),
            "n_iter": args.horizon_value,
            "q_online": r.get("q_online"),
            "q_fgla": r.get("q_fgla"),
            # build_e6_ledger.py / analyze_horizons.py dung ten 'beats';
            # failure_decomposition.json dung ten 'beats_fgla' -- doi ten,
            # khong doi gia tri.
            "beats": r.get("beats_fgla"),
            "final_edge_rel_error": r.get("final_edge_rel_error"),
            # giu lai cac truong goc them de tham chieu/audit, khong pha vo
            # gi neu script ha luu chi doc dung 6 key o tren
            "q_oracle0": r.get("q_oracle0"),
            "q_ratio_fgla": r.get("q_ratio_fgla"),
            "reject_fraction": r.get("reject_fraction"),
            "late_reject_fraction": r.get("late_reject_fraction"),
            "fallback_e1_failures": r.get("fallback_e1_failures"),
        })

    if missing_fields:
        print(f"CANH BAO: cac truong sau bi thieu o it nhat 1 case: {missing_fields}")
        print("Kiem tra lai schema cua failure_decomposition.json truoc khi dung ket qua nay.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"rows": rows}, indent=2, ensure_ascii=False))

    print(f"Da chuyen doi {len(rows)} case -> {out_path}")
    print(f"Horizon da tiem (co dinh, khong tu chon): n_iter = {args.horizon_value}")
    print("Vi du 1 dong sau khi chuyen doi:")
    print(json.dumps(rows[0], indent=2))


if __name__ == "__main__":
    main()
