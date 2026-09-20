#!/usr/bin/env python3
"""
compute_maturation.py
=======================
Tinh maturation metrics (T_edge_1pct, T_edge_0p5pct, T_edge_0p1pct) tu
`results/phase1d/tracking_traces.json`, dung dung dinh nghia trong handoff
muc 7 (B1):

    "For each case compute the first iteration after which the envelope
    estimate remains within each threshold for the rest of the valid tail."

Nguon du lieu THAT (da kiem tra):
    tracking_traces.json = list cac trace, moi trace co:
        {"config": str, "memory": int, "lambda_plus": float,
         "series": [{"iteration": int, "estimate": float, ...}, ...]}

CHI dung memory == FROZEN_MEMORY (mac dinh 3) cho phan tich chinh thuc --
memory=1,5 la ablation R1, tach rieng khong tron vao ket luan chinh (dung
nguyen tac "khong duoc dung ablation de thay the frozen primary method").

Nguong THRESHOLDS duoc KHOA truoc (1%, 0.5%, 0.1%) theo dung dinh nghia cua
handoff -- khong duoc doi sau khi xem ket qua dep/xau cho case nao.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Khoa truoc -- KHONG doi sau khi xem ket qua (rule 5/6 cua handoff)
THRESHOLDS = {"T_edge_1pct": 0.01, "T_edge_0p5pct": 0.005, "T_edge_0p1pct": 0.001}
FROZEN_MEMORY_DEFAULT = 3


def edge_rel_error_series(trace: dict) -> list[dict]:
    lam = trace["lambda_plus"]
    out = []
    for pt in trace["series"]:
        err = abs(pt["estimate"] - lam) / lam if lam != 0 else float("inf")
        out.append({"iteration": pt["iteration"], "edge_rel_error": err})
    return out


def maturation_time(series: list[dict], threshold: float):
    """Iteration dau tien ma edge_rel_error <= threshold VA GIU VAY den het
    trace (dung dinh nghia handoff: khong chi cham nguong 1 lan roi lai vuot
    ra -- phai la 'for the rest of the valid tail')."""
    n = len(series)
    for i in range(n):
        if all(series[j]["edge_rel_error"] <= threshold for j in range(i, n)):
            return series[i]["iteration"]
    return None  # khong bao gio on dinh trong pham vi trace -- ghi None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", required=True, help="Duong dan toi tracking_traces.json")
    ap.add_argument("--frozen-memory", type=int, default=FROZEN_MEMORY_DEFAULT,
                     help="Gia tri memory (p) chinh thuc da dong bang (mac dinh 3). "
                          "Cac trace memory khac se duoc ghi rieng vao 'ablation_other_memory'.")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    traces = json.loads(Path(args.traces).read_text())

    primary_rows = []
    ablation_rows = []

    for trace in traces:
        series = edge_rel_error_series(trace)
        row = {
            "config": trace["config"],
            "memory": trace["memory"],
            "lambda_plus": trace["lambda_plus"],
            "n_iterations_in_trace": len(series),
            "final_edge_rel_error": series[-1]["edge_rel_error"] if series else None,
        }
        for name, thr in THRESHOLDS.items():
            row[name] = maturation_time(series, thr)

        if trace["memory"] == args.frozen_memory:
            primary_rows.append(row)
        else:
            row["ablation_note"] = f"memory={trace['memory']} != frozen p={args.frozen_memory} (R1 ablation)"
            ablation_rows.append(row)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "thresholds_locked": THRESHOLDS,
        "frozen_memory": args.frozen_memory,
        "n_primary_cases": len(primary_rows),
        "n_ablation_rows": len(ablation_rows),
        "primary": primary_rows,
        "ablation_other_memory": ablation_rows,
        "data_limitation_note": (
            f"Chi co {len(primary_rows)} case o memory={args.frozen_memory} trong "
            f"tracking_traces.json hien tai -- khong du de phu 3 nhom co hoi "
            f"thap/vua/cao nhu Figure B1 yeu cau. Trace nay cung la Ritz thu dong "
            f"thuan tuy (chi co 'estimate'), KHONG co lambda_hat_envelope/"
            f"alpha/beta/gamma/safeguard_accept nhu dinh dang ly tuong trong "
            f"handoff muc 7 -- do la du lieu cua Phase-1D (passive), khong phai "
            f"trace cua online policy that (Phase-1E-R). Can bo sung trace "
            f"online that neu muon ve day du Figure B1/B2."
        ),
    }
    (out / "maturation_summary.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"Frozen memory = {args.frozen_memory}: {len(primary_rows)} case chinh thuc")
    for r in primary_rows:
        print(f"  {r['config']}: T_edge_1%={r['T_edge_1pct']}, "
              f"T_edge_0.5%={r['T_edge_0p5pct']}, T_edge_0.1%={r['T_edge_0p1pct']}, "
              f"final_edge_rel_error={r['final_edge_rel_error']:.3e}")
    print(f"Ablation (memory khac {args.frozen_memory}): {len(ablation_rows)} dong -- xem file de biet chi tiet")
    print(f"\nDa ghi: {out / 'maturation_summary.json'}")


if __name__ == "__main__":
    main()
