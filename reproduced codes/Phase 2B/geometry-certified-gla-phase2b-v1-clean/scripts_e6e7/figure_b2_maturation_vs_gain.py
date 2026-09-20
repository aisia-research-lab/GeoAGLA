#!/usr/bin/env python3
"""
figure_b2_maturation_vs_gain.py
=================================
Ve Figure B2 theo dung dinh nghia handoff muc 7 (B1):

    "Plot online gain at horizon H against estimator maturation ratio T_edge/H."
    Hypothesis: "Online acceleration is limited when estimator maturation
    consumes a large fraction of the available iteration budget."

Script nay CHU DONG kiem tra va BAO CAO RO RANG (khong im lang bo qua) 2 rui ro
da xac dinh truoc khi ve:

  1. Config trong maturation_summary.json (nguon: Phase-1D, tracking_traces.json)
     co the KHONG ton tai trong failure_decomposition.json (nguon: Phase-1E-R,
     online that) -- vi Phase-1D chay 6 config (them g32/h32) con Phase-1E-R
     chi chay 4 config (g16/h16/g24/h24). Case khong khop se bi BO QUA co ghi
     chu ro, khong lam gia du lieu.

  2. tracking_traces.json chi co it hon horizon dong bang H (vi du 219 < 360).
     Neu T_edge duoc quan sat gan sat cuoi trace ngan hon H, ty le T_edge/H se
     duoc tinh NHUNG kem theo canh bao "extrapolated_beyond_trace=True" -- vi
     khong chac chan uoc luong da giu on dinh tu do den H that.

Cach dung:
    python figure_b2_maturation_vs_gain.py \\
        --maturation results/e6_maturation/maturation_summary.json \\
        --failure-decomposition results/phase1er/failure_decomposition.json \\
        --horizon 360 \\
        --threshold-name T_edge_0p5pct \\
        --out results/e6_figure_b2
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--maturation", required=True)
    ap.add_argument("--failure-decomposition", required=True)
    ap.add_argument("--horizon", type=int, required=True,
                     help="Horizon dong bang H cua online policy (vi du 360). "
                          "PHAI la horizon that su da dong bang, khong tu chon.")
    ap.add_argument("--threshold-name", default="T_edge_0p5pct",
                     choices=["T_edge_1pct", "T_edge_0p5pct", "T_edge_0p1pct"],
                     help="Nguong T_edge dung de tinh ty le T_edge/H. "
                          "KHOA truoc, khong doi sau khi xem plot dep/xau.")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    mat = json.loads(Path(args.maturation).read_text())
    primary = mat["primary"]  # chi dung case da loc dung frozen memory

    fail = json.loads(Path(args.failure_decomposition).read_text())
    online_by_config: dict[str, list[dict]] = {}
    for r in fail:
        online_by_config.setdefault(r["config"], []).append(r)

    matched = []
    unmatched = []

    for case in primary:
        cfg = case["config"]
        t_edge = case[args.threshold_name]
        n_trace = case["n_iterations_in_trace"]

        if cfg not in online_by_config:
            unmatched.append({
                "config": cfg,
                "reason": f"khong tim thay config '{cfg}' trong failure_decomposition.json "
                          f"(Phase-1E-R co the chua chay config nay).",
            })
            continue

        if t_edge is None:
            unmatched.append({
                "config": cfg,
                "reason": f"{args.threshold_name} = None (khong bao gio on dinh trong pham vi trace).",
            })
            continue

        rows = online_by_config[cfg]
        # Gop nhieu seed/epsilon cua cung 1 config bang median -- T_edge chi co
        # 1 gia tri/config (khong theo seed) nen ap dung chung cho tat ca seed.
        q_online = statistics.median(r["q_online"] for r in rows)
        q_fgla = statistics.median(r["q_fgla"] for r in rows)
        online_gain = q_fgla - q_online  # dinh nghia delta_online tuong tu handoff muc 4

        extrapolated = n_trace < args.horizon

        matched.append({
            "config": cfg,
            "t_edge": t_edge,
            "n_trace": n_trace,
            "horizon": args.horizon,
            "maturation_ratio": t_edge / args.horizon,
            "q_online_median": q_online,
            "q_fgla_median": q_fgla,
            "online_gain": online_gain,
            "n_seeds_epsilons_averaged": len(rows),
            "extrapolated_beyond_trace": extrapolated,
            "extrapolation_note": (
                f"T_edge quan sat trong trace dai {n_trace} < horizon dong bang "
                f"{args.horizon} -- KHONG chac chan da on dinh tu {n_trace} den "
                f"{args.horizon}." if extrapolated else None
            ),
        })

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    summary = {
        "threshold_used": args.threshold_name,
        "horizon": args.horizon,
        "n_matched": len(matched),
        "n_unmatched": len(unmatched),
        "matched": matched,
        "unmatched": unmatched,
        "hypothesis_note": (
            "Hypothesis (handoff muc 7): Online acceleration bi gioi han khi "
            "estimator maturation chiem phan lon ngan sach vong lap. Day la "
            "GIA THUYET, khong phai ket luan chac chan -- dac biet voi co mau "
            f"n={len(matched)} nhu hien tai."
        ),
    }
    (out / "figure_b2_data.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"Khop duoc {len(matched)} case, khong khop {len(unmatched)} case.")
    for u in unmatched:
        print(f"  [BO QUA] {u['config']}: {u['reason']}")
    for m in matched:
        flag = " (EXTRAPOLATED -- xem ghi chu)" if m["extrapolated_beyond_trace"] else ""
        print(f"  [OK] {m['config']}: ratio={m['maturation_ratio']:.3f}, "
              f"online_gain={m['online_gain']:.4e}{flag}")

    if not matched:
        print("\nKHONG co case nao du du lieu ca 2 phia -- KHONG ve duoc Figure B2. Dung lai, khong bia du lieu.")
        return

    fig, ax = plt.subplots(figsize=(6.0, 4.6))
    for m in matched:
        marker = "^" if m["extrapolated_beyond_trace"] else "o"
        color = "tab:orange" if m["extrapolated_beyond_trace"] else "tab:blue"
        ax.scatter(m["maturation_ratio"], m["online_gain"], s=90, marker=marker, color=color)
        ax.annotate(m["config"], (m["maturation_ratio"], m["online_gain"]),
                     textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.axhline(0, color="gray", lw=1, linestyle="--")
    ax.set_xlabel(f"T_edge / H  (threshold={args.threshold_name}, H={args.horizon})")
    ax.set_ylabel("Online gain  (q_FGLA - q_Online, median)")
    ax.set_title(f"Figure B2 -- Maturation ratio vs. online gain (n={len(matched)})")
    if any(m["extrapolated_beyond_trace"] for m in matched):
        ax.text(0.02, 0.02,
                 "△ = T_edge extrapolated beyond observed trace length",
                 transform=ax.transAxes, fontsize=7, color="tab:orange")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(out / "B2_maturation_vs_gain.png", dpi=200)
    plt.close(fig)

    print(f"\nDa ghi: {out / 'figure_b2_data.json'}")
    print(f"Da ve: {out / 'B2_maturation_vs_gain.png'}")


if __name__ == "__main__":
    main()
