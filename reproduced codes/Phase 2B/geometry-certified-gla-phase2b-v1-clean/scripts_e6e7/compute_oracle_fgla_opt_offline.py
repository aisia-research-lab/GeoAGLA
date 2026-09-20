#!/usr/bin/env python3
"""
compute_oracle_fgla_opt_offline.py
====================================
Tinh HAU KY (post-hoc) 2 phuong phap con thieu trong basin_results.json cua
Phase-2B real-audio (chi co GLA/FGLA/Online) de du 5 phuong phap theo dung
yeu cau handoff muc 12:

    1. GLA                          -- da co (basin_results.json)
    2. FGLA thuc dung                -- da co (basin_results.json)
    3. FGLA-toi-uu-theo-oracle-lambda+ -- TINH O DAY
    4. Oracle minimax [lambda-, lambda+] -- TINH O DAY
    5. Online geometry-aware (frozen) -- da co (basin_results.json)

Cong thuc dung DUNG Theorem 8 / Corollary cua paper (khong doi logic khoa
hoc, chi ap dung cong thuc closed-form da duoc paper chung minh, tren
lambda_plus/lambda_minus da co san trong geometry_results.json):

    q_FGLA_opt(lambda_plus)      = 1 - sqrt(1 - lambda_plus)
    q_oracle_full(lambda_minus, lambda_plus) = nghiem dong dang Theorem 8
        (dung xap xi Corollary 10 khi lambda_minus ~ 0, hoac cong thuc day
         du neu ca 2 gia tri deu co)

KHONG chay lai engine, KHONG doi bat ky tham so online policy nao -- chi
doc geometry_results.json da co san lambda_plus/lambda_minus va tinh
them 2 cot moi.

Cach dung:
    python compute_oracle_fgla_opt_offline.py \\
        --geometry results/phase2b_even10pct_seed42/geometry_results.json \\
        --out results/phase2b_even10pct_seed42/oracle_fgla_opt_offline.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def q_fgla_opt(lambda_plus: float) -> float:
    """FGLA toi uu hang so, Theorem 8 khi gamma=1 (tuong duong FGLA)."""
    if lambda_plus is None or not (0 <= lambda_plus < 1):
        return None
    return 1.0 - math.sqrt(1.0 - lambda_plus)


def q_oracle_conservative(lambda_plus: float) -> float:
    """
    Oracle bao thu tren khoang [0, lambda_plus] -- CHI can lambda_plus, khong
    can lambda_minus. Dung Corollary 10 (paper ICLR2027 Geometry Determines
    Acceleration in Phase Retrieval):

        q*(0, l+) = [3 - l+ - sqrt((1-l+)(9-l+))] / 2

    Day la lua chon THUC TE cho du lieu hien co, vi geometry_results.json
    cua engine goc KHONG xuat lambda_minus.
    """
    if lambda_plus is None or not (0 <= lambda_plus < 1):
        return None
    return (3 - lambda_plus - math.sqrt((1 - lambda_plus) * (9 - lambda_plus))) / 2


def q_oracle_full(lambda_minus: float, lambda_plus: float) -> float:
    """
    Nghiem minimax day du Theorem 8 cho khoang [lambda_minus, lambda_plus].
    Dung dung cong thuc dong (closed-form) da duoc chung minh trong paper
    "Geometry Determines Acceleration in Phase Retrieval" (Theorem 8),
    KHONG suy dien lai tu dau.

    q*(l-, l+) = [B - sqrt(B^2 - 4 l+ (l+ - l-)^2)] / [2 (l+ - l-)]
    voi D = l+ - l-, B = 3 l+ + l- - l+^2 - 3 l+ l-
    """
    if lambda_plus is None or lambda_minus is None:
        return None
    if not (0 <= lambda_minus <= lambda_plus < 1):
        return None
    D = lambda_plus - lambda_minus
    if D < 1e-12:
        # gan suy bien ve 1 diem -- dung gioi han D->0: q* -> 0 (Corollary 11)
        return 0.0
    B = 3 * lambda_plus + lambda_minus - lambda_plus ** 2 - 3 * lambda_plus * lambda_minus
    disc = B ** 2 - 4 * lambda_plus * D ** 2
    if disc < 0:
        return None  # cong thuc khong hop le voi cap (l-, l+) nay -- ghi None, khong ep so
    return (B - math.sqrt(disc)) / (2 * D)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--geometry", required=True, help="Duong dan toi geometry_results.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = json.loads(Path(args.geometry).read_text())
    out_rows = []
    n_missing_lambda_minus = 0

    for r in rows:
        lp = r.get("lambda_plus")
        lm = r.get("lambda_minus")  # co the KHONG co san trong geometry_results.json hien tai
        if lm is None:
            n_missing_lambda_minus += 1

        out_rows.append({
            "file": r.get("file"),
            "profile": r.get("profile"),
            "lambda_plus": lp,
            "lambda_minus": lm,
            "q_gla_pred": lp,  # q_GLA = lambda_plus (Theorem 8, dinh nghia)
            "q_fgla_opt_pred": q_fgla_opt(lp),
            "q_oracle_conservative_pred": q_oracle_conservative(lp),
            "q_oracle_full_pred": q_oracle_full(lm, lp) if lm is not None else None,
            "oracle_note": (
                None if lm is not None else
                "lambda_minus khong co san trong geometry_results.json hien tai -- "
                "dung q_oracle_conservative_pred (chi can lambda_plus, Corollary 10) "
                "thay cho q_oracle_full_pred. Neu can oracle day du [l-,l+], phai bo "
                "sung xuat lambda_minus tu engine goc (khong tu uoc luong tu du lieu khac)."
            ),
        })

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "n_cases": len(out_rows),
        "n_missing_lambda_minus": n_missing_lambda_minus,
        "rows": out_rows,
        "formula_source": "Theorem 8, paper ICLR2027 Geometry Determines Acceleration in Phase Retrieval",
        "warning": (
            f"{n_missing_lambda_minus}/{len(out_rows)} case thieu lambda_minus -- "
            "q_oracle_full_pred = None cho cac case nay. Kiem tra xem engine goc "
            "co xuat lambda_minus khong truoc khi coi day la du lieu day du cho "
            "5-phuong-phap-so-sanh theo yeu cau handoff muc 12."
        ) if n_missing_lambda_minus else None,
    }
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print(f"Da tinh {len(out_rows)} case, {n_missing_lambda_minus} thieu lambda_minus.")
    print(f"Da ghi: {out_path}")
    if n_missing_lambda_minus:
        print(f"\nCANH BAO: {result['warning']}")


if __name__ == "__main__":
    main()
