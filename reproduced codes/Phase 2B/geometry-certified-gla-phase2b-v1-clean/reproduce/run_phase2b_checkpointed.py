# #!/usr/bin/env python3
# """
# run_phase2b_checkpointed.py
# ============================
# Wrapper quanh `experiments.phase2b_real_audio.run.run()` để CHIA NHỎ danh sách
# file audio thành nhiều "batch" độc lập — mỗi batch tự ghi kết quả xuống đĩa
# ngay khi xong — nhằm đảm bảo KHÔNG MẤT kết quả nếu phiên chạy (Kaggle, giới
# hạn ~12h, hoặc bất kỳ máy nào) bị ngắt giữa chừng.

# KHÔNG có dòng nào trong experiments/phase2b_real_audio/run.py bị sửa.
# Script này chỉ IMPORT và GỌI LẠI đúng hàm run() gốc cho từng batch nhỏ, sau đó
# gộp (merge) các JSON/CSV bằng ĐÚNG công thức gate/summary/figure đã có sẵn
# trong run.py (copy y nguyên phần tổng hợp cuối — không đổi bất kỳ công thức
# khoa học nào, chỉ áp dụng nó lên dữ liệu đã gộp từ nhiều batch thay vì một
# lần chạy độc khối).

# Cơ chế resume: mỗi batch ghi `out/_batch_NN/summary.json` khi hoàn tất. Lần
# chạy lại (kể cả ở phiên Kaggle hoàn toàn mới, miễn giữ lại thư mục `out/`)
# sẽ tự động BỎ QUA các batch đã có summary.json và chỉ chạy tiếp các batch
# còn thiếu.

# Cách dùng:
#     # Preflight nhỏ (khuyến nghị chạy trước để đo thời gian/file)
#     python -m reproduce.run_phase2b_checkpointed \\
#         --audio-dir data/my_audio --max-files 2 --batch-size 2 \\
#         --out results/phase2b_preflight

#     # Chạy chính thức, chia 2 file/batch -> 3 batch cho 6 file
#     python -m reproduce.run_phase2b_checkpointed \\
#         --audio-dir data/my_audio --max-files 6 --batch-size 2 \\
#         --out results/phase2b

#     # Bị ngắt giữa chừng? Chạy lại y nguyên lệnh trên -> batch đã xong tự skip
# """
# from __future__ import annotations

# import argparse
# import csv
# import json
# import shutil
# import sys
# import time
# from pathlib import Path

# import numpy as np
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt

# ROOT = Path(__file__).resolve().parents[1]
# for _p in (ROOT, ROOT / "src"):
#     if str(_p) not in sys.path:
#         sys.path.insert(0, str(_p))

# from experiments.phase2b_real_audio.run import run as run_phase2b_batch  # noqa: E402


# # ---------------------------------------------------------------------------
# # 1. Liệt kê + chia batch (deterministic — cùng logic sort/slice như run.py)
# # ---------------------------------------------------------------------------

# def discover_wav_files(audio_dir: Path, max_files):
#     paths = sorted(
#         p for p in Path(audio_dir).rglob("*")
#         if p.is_file() and p.suffix.lower() == ".wav"
#     )
#     if max_files is not None:
#         paths = paths[: int(max_files)]
#     return paths


# def chunk(paths, batch_size):
#     return [paths[i:i + batch_size] for i in range(0, len(paths), batch_size)]


# # ---------------------------------------------------------------------------
# # 2. Chạy từng batch qua đúng hàm run() gốc — có khả năng resume
# # ---------------------------------------------------------------------------

# def run_batches(paths, config_path, out_root: Path, batch_size: int,
#                  deadline: float | None = None):
#     """
#     deadline: mốc thời gian tuyệt đối (time.time() + budget), KHÔNG phải số
#     giây. Trước khi bắt đầu MỖI batch mới, kiểm tra: nếu đã qua deadline thì
#     DỪNG NGAY (không bắt đầu batch dở dang), trả về danh sách batch đã xong
#     kèm cờ "stopped_early=True" để caller biết và vẫn tiến hành merge() bình
#     thường trên phần đã có — đảm bảo notebook luôn kết thúc "sạch" (exit 0),
#     Kaggle luôn lưu được Output, KHÔNG bao giờ bị giết giữa chừng mất trắng.
#     """
#     batches = chunk(paths, batch_size)
#     batch_out_dirs = []
#     stopped_early = False
#     for i, batch_files in enumerate(batches):
#         batch_out = out_root / f"_batch_{i:02d}"
#         marker = batch_out / "summary.json"

#         if marker.exists():
#             batch_out_dirs.append(batch_out)
#             print(f"[batch {i+1}/{len(batches)}] Đã hoàn tất trước đó — bỏ qua ({marker}).", flush=True)
#             continue

#         if deadline is not None and time.time() >= deadline:
#             remaining = len(batches) - i
#             print(f"\n!!! HẾT NGÂN SÁCH THỜI GIAN — dừng an toàn trước batch {i+1}/{len(batches)}.")
#             print(f"!!! Còn {remaining} batch chưa chạy — sẽ chạy tiếp ở phiên sau (resume).")
#             stopped_early = True
#             break

#         batch_audio_dir = out_root / f"_audio_batch_{i:02d}"
#         if batch_audio_dir.exists():
#             shutil.rmtree(batch_audio_dir)
#         batch_audio_dir.mkdir(parents=True, exist_ok=True)
#         for f in batch_files:
#             shutil.copy2(f, batch_audio_dir / f.name)

#         names = ", ".join(f.name for f in batch_files)
#         print(f"[batch {i+1}/{len(batches)}] Đang chạy ({names}) ...", flush=True)
#         t0 = time.time()
#         run_phase2b_batch(str(batch_audio_dir), config_path, str(batch_out), max_files=len(batch_files))
#         print(f"[batch {i+1}/{len(batches)}] Xong sau {time.time()-t0:.1f}s. Đã ghi: {marker}", flush=True)
#         batch_out_dirs.append(batch_out)

#     return batch_out_dirs, stopped_early


# # ---------------------------------------------------------------------------
# # 3. Gộp kết quả — công thức gate/summary/figure GIỮ NGUYÊN như run.py
# #    (copy verbatim từ dòng "gok=..." trở xuống trong run.py, không đổi logic)
# # ---------------------------------------------------------------------------

# def _load(path: Path, default):
#     return json.loads(path.read_text()) if path.exists() else default


# def merge(batch_out_dirs, config_path: str, out_root: Path):
#     C = json.loads(Path(config_path).read_text())
#     manifest, geometry, basin = [], [], []
#     for bd in batch_out_dirs:
#         manifest.extend(_load(bd / "audio_manifest.json", []))
#         geometry.extend(_load(bd / "geometry_results.json", []))
#         basin.extend(_load(bd / "basin_results.json", []))

#     out = out_root
#     (out / "figures").mkdir(parents=True, exist_ok=True)
#     (out / "audio_manifest.json").write_text(json.dumps(manifest, indent=2))
#     (out / "geometry_results.json").write_text(json.dumps(geometry, indent=2, allow_nan=True))
#     (out / "basin_results.json").write_text(json.dumps(basin, indent=2, allow_nan=True))
#     for name, rows in [("geometry_results.csv", geometry), ("basin_results.csv", basin)]:
#         if rows:
#             with (out / name).open("w", newline="") as f:
#                 fields = sorted(set().union(*(r.keys() for r in rows)))
#                 w = csv.DictWriter(f, fieldnames=fields)
#                 w.writeheader(); w.writerows(rows)

#     gok = [r for r in geometry if r.get("status") == "OK"]
#     if not gok:
#         summary = {"phase2b_gate": "RED", "reason": "no regular real-audio geometry cases", "n_files": len(manifest)}
#         (out / "summary.json").write_text(json.dumps(summary, indent=2))
#         print(json.dumps(summary, indent=2))
#         return summary

#     paired = [r for r in basin if r["success_online"] and r["success_fgla"] and r["q_ratio_online_fgla"] is not None]
#     small = [r for r in basin if (r["init_kind"] == "transverse" and r["level"] <= 0.01)
#              or (r["init_kind"] == "phase_jitter" and r["level"] <= 0.15)]
#     ratios = np.asarray([r["q_ratio_online_fgla"] for r in paired], float) if paired else np.asarray([])
#     edges = np.asarray([r["final_edge_rel_error"] for r in basin if r["final_edge_rel_error"] is not None], float)
#     G = C["gates"]
#     geom_max = float(np.max([r["geometry_rel_error"] for r in gok]))
#     edge_med = float(np.median(edges)) if edges.size else float("inf")
#     small_succ = float(np.mean([r["success_online"] for r in small])) if small else 0.0
#     on_succ = float(np.mean([r["success_online"] for r in basin])) if basin else 0.0
#     fg_succ = float(np.mean([r["success_fgla"] for r in basin])) if basin else 0.0
#     beat = float(np.mean([r["beats_fgla"] for r in paired])) if paired else 0.0
#     medratio = float(np.median(ratios)) if ratios.size else float("inf")
#     late = float(np.mean([r["late_reject_fraction"] for r in basin])) if basin else 1.0
#     e1 = int(sum(r["fallback_e1_failures"] for r in basin))
#     passes = {
#         "G2B_A_real_audio_geometry_pass": bool(geom_max <= G["geometry_relative_error_max"]),
#         "G2B_B_active_edge_tracking_pass": bool(edge_med <= G["edge_relative_error_median_max"]),
#         "G2B_C_small_basin_pass": bool(small_succ >= G["small_basin_success_fraction_min"]),
#         "G2B_D_basin_nonshrink_pass": bool(on_succ + G["online_basin_deficit_vs_fgla_max"] >= fg_succ),
#         "G2B_E_paired_rate_pass": bool(len(paired) > 0 and beat >= G["paired_success_online_beat_fraction_min"]
#                                         and medratio < G["paired_success_median_q_ratio_max"]),
#         "G2B_F_safeguard_pass": bool(late <= G["late_reject_fraction_mean_max"] and e1 <= G["fallback_e1_failures_max"]),
#     }
#     summary = {
#         "profile": C["profile"], "n_files": len(manifest), "n_geometry_cases": len(gok),
#         "n_basin_runs": len(basin), "n_paired_success_runs": len(paired),
#         "max_geometry_relative_error": geom_max, "median_final_edge_relative_error": edge_med,
#         "small_basin_online_success_fraction": small_succ, "overall_online_success_fraction": on_succ,
#         "overall_fgla_success_fraction": fg_succ, "paired_success_online_beat_fraction": beat,
#         "paired_success_median_q_ratio": medratio,
#         "paired_success_p90_q_ratio": float(np.percentile(ratios, 90)) if ratios.size else None,
#         "mean_late_reject_fraction": late, "fallback_e1_failures": e1,
#         "near_phase_degenerate_fraction": float(np.mean([r["lambda_plus"] >= 0.9999 for r in gok])),
#         **passes,
#     }
#     summary["phase2b_gate"] = "GREEN" if all(passes.values()) else "YELLOW"
#     summary["merged_from_batches"] = len(batch_out_dirs)
#     (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=True))

#     groups = []
#     for kind in sorted(set(r["init_kind"] for r in basin)):
#         for level in sorted(set(r["level"] for r in basin if r["init_kind"] == kind)):
#             z = [r for r in basin if r["init_kind"] == kind and r["level"] == level]
#             pair = [r for r in z if r["success_online"] and r["success_fgla"] and r["q_ratio_online_fgla"] is not None]
#             groups.append({
#                 "init_kind": kind, "level": level, "n": len(z),
#                 "online_success_fraction": float(np.mean([r["success_online"] for r in z])),
#                 "fgla_success_fraction": float(np.mean([r["success_fgla"] for r in z])),
#                 "paired_beat_fraction": float(np.mean([r["beats_fgla"] for r in pair])) if pair else None,
#                 "paired_median_q_ratio": float(np.median([r["q_ratio_online_fgla"] for r in pair])) if pair else None,
#             })
#     (out / "initialization_summary.json").write_text(json.dumps(groups, indent=2, allow_nan=True))

#     labels = [f"{r['file']}\n{r['profile']}" for r in gok]
#     x = np.arange(len(gok))
#     fig, ax = plt.subplots(figsize=(max(8, 1.1 * len(gok)), 4.8))
#     ax.bar(x, [r["geometry_rel_error"] for r in gok]); ax.axhline(G["geometry_relative_error_max"], linestyle="--")
#     ax.set_yscale("log"); ax.set_xticks(x, labels, rotation=35, ha="right"); ax.set_ylabel("relative error")
#     ax.set_title("2B-D1 — Real-audio tangent geometry transfer (merged batches)")
#     fig.tight_layout(); fig.savefig(out / "figures" / "2B_D1_real_audio_geometry.png", dpi=180); plt.close(fig)

#     fig, ax = plt.subplots(figsize=(7.5, 4.8))
#     for kind in sorted(set(g["init_kind"] for g in groups)):
#         z = [g for g in groups if g["init_kind"] == kind]
#         ax.plot([g["level"] for g in z], [g["online_success_fraction"] for g in z], marker="o", label=f"{kind} online")
#         ax.plot([g["level"] for g in z], [g["fgla_success_fraction"] for g in z], marker="x", label=f"{kind} FGLA")
#     ax.set_xscale("log"); ax.set_ylim(-.02, 1.02); ax.set_xlabel("initialization level"); ax.set_ylabel("basin success fraction")
#     ax.set_title("2B-D2 — Real-audio basin profile (merged batches)"); ax.legend(fontsize=8)
#     fig.tight_layout(); fig.savefig(out / "figures" / "2B_D2_basin_profile.png", dpi=180); plt.close(fig)

#     if paired:
#         fig, ax = plt.subplots(figsize=(7.5, 4.8))
#         ax.hist([r["q_ratio_online_fgla"] for r in paired], bins=min(12, max(4, len(paired) // 2)))
#         ax.axvline(1.0, linestyle="--"); ax.set_xlabel("q_online / q_FGLA"); ax.set_ylabel("count")
#         ax.set_title("2B-D3 — Paired-success local rate transfer (merged batches)")
#         fig.tight_layout(); fig.savefig(out / "figures" / "2B_D3_rate_ratio.png", dpi=180); plt.close(fig)

#     print(f"Đã gộp {len(batch_out_dirs)} batch -> {out}")
#     print(json.dumps(summary, indent=2))
#     return summary


# def main():
#     ap = argparse.ArgumentParser(
#         description="Phase-2B real-audio runner có checkpoint theo batch file audio; "
#                     "dùng lại nguyên hàm run() gốc, không sửa code khoa học."
#     )
#     ap.add_argument("--audio-dir", required=True)
#     ap.add_argument("--config", default="configs/phase2b_grid.json")
#     ap.add_argument("--out", default="results/phase2b")
#     ap.add_argument("--max-files", type=int, default=None)
#     ap.add_argument("--batch-size", type=int, default=2, help="Số file audio xử lý mỗi batch (mặc định 2).")
#     ap.add_argument(
#         "--time-budget-sec", type=float, default=None,
#         help="Ngân sách thời gian TỐI ĐA (giây) cho lần gọi này. Trước mỗi batch "
#              "mới, script tự kiểm tra thời gian đã trôi qua; nếu vượt ngân sách, "
#              "DỪNG AN TOÀN (không bắt đầu batch dở), vẫn merge() phần đã có, và "
#              "thoát với exit code 0 (không phải lỗi) -- để Kaggle/CI luôn lưu "
#              "được Output thay vì bị giết giữa chừng mất trắng. Khuyến nghị đặt "
#              "thấp hơn giới hạn phiên thật ít nhất 1-1.5h (dự phòng cho phần "
#              "cài đặt + merge + zip + commit ở cuối)."
#     )
#     args = ap.parse_args()

#     out_root = Path(args.out)
#     out_root.mkdir(parents=True, exist_ok=True)

#     all_paths = discover_wav_files(Path(args.audio_dir), args.max_files)
#     if not all_paths:
#         raise FileNotFoundError(f"Không tìm thấy file .wav nào trong {args.audio_dir}")
#     n_batches = ((len(all_paths) - 1) // args.batch_size) + 1
#     print(f"Tìm thấy {len(all_paths)} file WAV -> chia thành {n_batches} batch (batch-size={args.batch_size}).")

#     deadline = (time.time() + args.time_budget_sec) if args.time_budget_sec is not None else None
#     if deadline is not None:
#         print(f"Ngân sách thời gian: {args.time_budget_sec/3600:.2f}h -- sẽ tự dừng an toàn nếu chạm mốc.")

#     batch_out_dirs, stopped_early = run_batches(all_paths, args.config, out_root, args.batch_size, deadline)
#     result = merge(batch_out_dirs, args.config, out_root)
#     if isinstance(result, dict):
#         result["partial_run_stopped_early"] = stopped_early
#         result["n_batches_done"] = len(batch_out_dirs)
#         result["n_batches_target"] = n_batches
#         (out_root / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=True))

#     if stopped_early:
#         print(f"\nLƯU Ý: dừng sớm theo ngân sách thời gian -- summary.json hiện tại"
#               f" chỉ phản ánh {len(batch_out_dirs)}/{n_batches} batch. Chạy lại"
#               f" lệnh này (không đổi tham số) ở phiên sau để tiếp tục phần còn lại.")


# if __name__ == "__main__":
#     main()


#!/usr/bin/env python3
"""
run_phase2b_checkpointed.py
============================
Wrapper quanh `experiments.phase2b_real_audio.run.run()` để CHIA NHỎ danh sách
file audio thành nhiều "batch" độc lập — mỗi batch tự ghi kết quả xuống đĩa
ngay khi xong — nhằm đảm bảo KHÔNG MẤT kết quả nếu phiên chạy (Kaggle, giới
hạn ~12h, hoặc bất kỳ máy nào) bị ngắt giữa chừng.

KHÔNG có dòng nào trong experiments/phase2b_real_audio/run.py bị sửa.
Script này chỉ IMPORT và GỌI LẠI đúng hàm run() gốc cho từng batch nhỏ, sau đó
gộp (merge) các JSON/CSV bằng ĐÚNG công thức gate/summary/figure đã có sẵn
trong run.py (copy y nguyên phần tổng hợp cuối — không đổi bất kỳ công thức
khoa học nào, chỉ áp dụng nó lên dữ liệu đã gộp từ nhiều batch thay vì một
lần chạy độc khối).

Cơ chế resume: mỗi batch ghi `out/_batch_NN/summary.json` khi hoàn tất. Lần
chạy lại (kể cả ở phiên Kaggle hoàn toàn mới, miễn giữ lại thư mục `out/`)
sẽ tự động BỎ QUA các batch đã có summary.json và chỉ chạy tiếp các batch
còn thiếu.

Cách dùng:
    # Preflight nhỏ (khuyến nghị chạy trước để đo thời gian/file)
    python -m reproduce.run_phase2b_checkpointed \\
        --audio-dir data/my_audio --max-files 2 --batch-size 2 \\
        --out results/phase2b_preflight

    # Chạy chính thức, chia 2 file/batch -> 3 batch cho 6 file
    python -m reproduce.run_phase2b_checkpointed \\
        --audio-dir data/my_audio --max-files 6 --batch-size 2 \\
        --out results/phase2b

    # Bị ngắt giữa chừng? Chạy lại y nguyên lệnh trên -> batch đã xong tự skip
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from experiments.phase2b_real_audio.run import run as run_phase2b_batch  # noqa: E402


# ---------------------------------------------------------------------------
# 1. Liệt kê + chia batch (deterministic — cùng logic sort/slice như run.py)
# ---------------------------------------------------------------------------

def discover_wav_files(audio_dir: Path, max_files):
    paths = sorted(
        p for p in Path(audio_dir).rglob("*")
        if p.is_file() and p.suffix.lower() == ".wav"
    )
    if max_files is not None:
        paths = paths[: int(max_files)]
    return paths


def chunk(paths, batch_size):
    return [paths[i:i + batch_size] for i in range(0, len(paths), batch_size)]


# ---------------------------------------------------------------------------
# 2. Chạy từng batch qua đúng hàm run() gốc — có khả năng resume
# ---------------------------------------------------------------------------

def run_batches(paths, config_path, out_root: Path, batch_size: int,
                 deadline: float | None = None):
    """
    deadline: mốc thời gian tuyệt đối (time.time() + budget), KHÔNG phải số
    giây. Trước khi bắt đầu MỖI batch mới, kiểm tra: nếu đã qua deadline thì
    DỪNG NGAY (không bắt đầu batch dở dang), trả về danh sách batch đã xong
    kèm cờ "stopped_early=True" để caller biết và vẫn tiến hành merge() bình
    thường trên phần đã có — đảm bảo notebook luôn kết thúc "sạch" (exit 0),
    Kaggle luôn lưu được Output, KHÔNG bao giờ bị giết giữa chừng mất trắng.
    """
    batches = chunk(paths, batch_size)
    batch_out_dirs = []
    stopped_early = False
    for i, batch_files in enumerate(batches):
        batch_out = out_root / f"_batch_{i:02d}"
        marker = batch_out / "summary.json"

        if marker.exists():
            batch_out_dirs.append(batch_out)
            print(f"[batch {i+1}/{len(batches)}] Đã hoàn tất trước đó — bỏ qua ({marker}).", flush=True)
            continue

        if deadline is not None and time.time() >= deadline:
            remaining = len(batches) - i
            print(f"\n!!! HẾT NGÂN SÁCH THỜI GIAN — dừng an toàn trước batch {i+1}/{len(batches)}.")
            print(f"!!! Còn {remaining} batch chưa chạy — sẽ chạy tiếp ở phiên sau (resume).")
            stopped_early = True
            break

        batch_audio_dir = out_root / f"_audio_batch_{i:02d}"
        if batch_audio_dir.exists():
            shutil.rmtree(batch_audio_dir)
        batch_audio_dir.mkdir(parents=True, exist_ok=True)
        for f in batch_files:
            shutil.copy2(f, batch_audio_dir / f.name)

        names = ", ".join(f.name for f in batch_files)
        print(f"[batch {i+1}/{len(batches)}] Đang chạy ({names}) ...", flush=True)
        t0 = time.time()
        run_phase2b_batch(str(batch_audio_dir), config_path, str(batch_out), max_files=len(batch_files))
        print(f"[batch {i+1}/{len(batches)}] Xong sau {time.time()-t0:.1f}s. Đã ghi: {marker}", flush=True)
        batch_out_dirs.append(batch_out)

    return batch_out_dirs, stopped_early


# ---------------------------------------------------------------------------
# 3. Gộp kết quả — công thức gate/summary/figure GIỮ NGUYÊN như run.py
#    (copy verbatim từ dòng "gok=..." trở xuống trong run.py, không đổi logic)
# ---------------------------------------------------------------------------

def _load(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def merge(batch_out_dirs, config_path: str, out_root: Path):
    C = json.loads(Path(config_path).read_text())
    manifest, geometry, basin = [], [], []
    for bd in batch_out_dirs:
        manifest.extend(_load(bd / "audio_manifest.json", []))
        geometry.extend(_load(bd / "geometry_results.json", []))
        basin.extend(_load(bd / "basin_results.json", []))

    out = out_root
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "audio_manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "geometry_results.json").write_text(json.dumps(geometry, indent=2, allow_nan=True))
    (out / "basin_results.json").write_text(json.dumps(basin, indent=2, allow_nan=True))
    for name, rows in [("geometry_results.csv", geometry), ("basin_results.csv", basin)]:
        if rows:
            with (out / name).open("w", newline="") as f:
                fields = sorted(set().union(*(r.keys() for r in rows)))
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader(); w.writerows(rows)

    gok = [r for r in geometry if r.get("status") == "OK"]
    if not gok:
        summary = {"phase2b_gate": "RED", "reason": "no regular real-audio geometry cases", "n_files": len(manifest)}
        (out / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        return summary

    paired = [r for r in basin if r["success_online"] and r["success_fgla"] and r["q_ratio_online_fgla"] is not None]
    small = [r for r in basin if (r["init_kind"] == "transverse" and r["level"] <= 0.01)
             or (r["init_kind"] == "phase_jitter" and r["level"] <= 0.15)]
    ratios = np.asarray([r["q_ratio_online_fgla"] for r in paired], float) if paired else np.asarray([])
    edges = np.asarray([r["final_edge_rel_error"] for r in basin if r["final_edge_rel_error"] is not None], float)
    G = C["gates"]
    geom_max = float(np.max([r["geometry_rel_error"] for r in gok]))
    edge_med = float(np.median(edges)) if edges.size else float("inf")
    small_succ = float(np.mean([r["success_online"] for r in small])) if small else 0.0
    on_succ = float(np.mean([r["success_online"] for r in basin])) if basin else 0.0
    fg_succ = float(np.mean([r["success_fgla"] for r in basin])) if basin else 0.0
    beat = float(np.mean([r["beats_fgla"] for r in paired])) if paired else 0.0
    medratio = float(np.median(ratios)) if ratios.size else float("inf")
    late = float(np.mean([r["late_reject_fraction"] for r in basin])) if basin else 1.0
    e1 = int(sum(r["fallback_e1_failures"] for r in basin))
    passes = {
        "G2B_A_real_audio_geometry_pass": bool(geom_max <= G["geometry_relative_error_max"]),
        "G2B_B_active_edge_tracking_pass": bool(edge_med <= G["edge_relative_error_median_max"]),
        "G2B_C_small_basin_pass": bool(small_succ >= G["small_basin_success_fraction_min"]),
        "G2B_D_basin_nonshrink_pass": bool(on_succ + G["online_basin_deficit_vs_fgla_max"] >= fg_succ),
        "G2B_E_paired_rate_pass": bool(len(paired) > 0 and beat >= G["paired_success_online_beat_fraction_min"]
                                        and medratio < G["paired_success_median_q_ratio_max"]),
        "G2B_F_safeguard_pass": bool(late <= G["late_reject_fraction_mean_max"] and e1 <= G["fallback_e1_failures_max"]),
    }
    summary = {
        "profile": C["profile"], "n_files": len(manifest), "n_geometry_cases": len(gok),
        "n_basin_runs": len(basin), "n_paired_success_runs": len(paired),
        "max_geometry_relative_error": geom_max, "median_final_edge_relative_error": edge_med,
        "small_basin_online_success_fraction": small_succ, "overall_online_success_fraction": on_succ,
        "overall_fgla_success_fraction": fg_succ, "paired_success_online_beat_fraction": beat,
        "paired_success_median_q_ratio": medratio,
        "paired_success_p90_q_ratio": float(np.percentile(ratios, 90)) if ratios.size else None,
        "mean_late_reject_fraction": late, "fallback_e1_failures": e1,
        "near_phase_degenerate_fraction": float(np.mean([r["lambda_plus"] >= 0.9999 for r in gok])),
        **passes,
    }
    summary["phase2b_gate"] = "GREEN" if all(passes.values()) else "YELLOW"
    summary["merged_from_batches"] = len(batch_out_dirs)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=True))

    groups = []
    for kind in sorted(set(r["init_kind"] for r in basin)):
        for level in sorted(set(r["level"] for r in basin if r["init_kind"] == kind)):
            z = [r for r in basin if r["init_kind"] == kind and r["level"] == level]
            pair = [r for r in z if r["success_online"] and r["success_fgla"] and r["q_ratio_online_fgla"] is not None]
            groups.append({
                "init_kind": kind, "level": level, "n": len(z),
                "online_success_fraction": float(np.mean([r["success_online"] for r in z])),
                "fgla_success_fraction": float(np.mean([r["success_fgla"] for r in z])),
                "paired_beat_fraction": float(np.mean([r["beats_fgla"] for r in pair])) if pair else None,
                "paired_median_q_ratio": float(np.median([r["q_ratio_online_fgla"] for r in pair])) if pair else None,
            })
    (out / "initialization_summary.json").write_text(json.dumps(groups, indent=2, allow_nan=True))

    labels = [f"{r['file']}\n{r['profile']}" for r in gok]
    x = np.arange(len(gok))
    fig, ax = plt.subplots(figsize=(max(8, 1.1 * len(gok)), 4.8))
    ax.bar(x, [r["geometry_rel_error"] for r in gok]); ax.axhline(G["geometry_relative_error_max"], linestyle="--")
    ax.set_yscale("log"); ax.set_xticks(x, labels, rotation=35, ha="right"); ax.set_ylabel("relative error")
    ax.set_title("2B-D1 — Real-audio tangent geometry transfer (merged batches)")
    fig.tight_layout(); fig.savefig(out / "figures" / "2B_D1_real_audio_geometry.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    for kind in sorted(set(g["init_kind"] for g in groups)):
        z = [g for g in groups if g["init_kind"] == kind]
        ax.plot([g["level"] for g in z], [g["online_success_fraction"] for g in z], marker="o", label=f"{kind} online")
        ax.plot([g["level"] for g in z], [g["fgla_success_fraction"] for g in z], marker="x", label=f"{kind} FGLA")
    ax.set_xscale("log"); ax.set_ylim(-.02, 1.02); ax.set_xlabel("initialization level"); ax.set_ylabel("basin success fraction")
    ax.set_title("2B-D2 — Real-audio basin profile (merged batches)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(out / "figures" / "2B_D2_basin_profile.png", dpi=180); plt.close(fig)

    if paired:
        fig, ax = plt.subplots(figsize=(7.5, 4.8))
        ax.hist([r["q_ratio_online_fgla"] for r in paired], bins=min(12, max(4, len(paired) // 2)))
        ax.axvline(1.0, linestyle="--"); ax.set_xlabel("q_online / q_FGLA"); ax.set_ylabel("count")
        ax.set_title("2B-D3 — Paired-success local rate transfer (merged batches)")
        fig.tight_layout(); fig.savefig(out / "figures" / "2B_D3_rate_ratio.png", dpi=180); plt.close(fig)

    print(f"Đã gộp {len(batch_out_dirs)} batch -> {out}")
    print(json.dumps(summary, indent=2))
    return summary


def main():
    ap = argparse.ArgumentParser(
        description="Phase-2B real-audio runner có checkpoint theo batch file audio; "
                    "dùng lại nguyên hàm run() gốc, không sửa code khoa học."
    )
    ap.add_argument("--audio-dir", required=True)
    ap.add_argument("--config", default="configs/phase2b_grid.json")
    ap.add_argument("--out", default="results/phase2b")
    ap.add_argument("--max-files", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=2, help="Số file audio xử lý mỗi batch (mặc định 2).")
    ap.add_argument(
        "--time-budget-sec", type=float, default=None,
        help="Ngân sách thời gian TỐI ĐA (giây) cho lần gọi này. Trước mỗi batch "
             "mới, script tự kiểm tra thời gian đã trôi qua; nếu vượt ngân sách, "
             "DỪNG AN TOÀN (không bắt đầu batch dở), vẫn merge() phần đã có, và "
             "thoát với exit code 0 (không phải lỗi) -- để Kaggle/CI luôn lưu "
             "được Output thay vì bị giết giữa chừng mất trắng. Khuyến nghị đặt "
             "thấp hơn giới hạn phiên thật ít nhất 1-1.5h (dự phòng cho phần "
             "cài đặt + merge + zip + commit ở cuối)."
    )
    args = ap.parse_args()

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    all_paths = discover_wav_files(Path(args.audio_dir), args.max_files)
    if not all_paths:
        raise FileNotFoundError(f"Không tìm thấy file .wav nào trong {args.audio_dir}")
    n_batches = ((len(all_paths) - 1) // args.batch_size) + 1
    print(f"Tìm thấy {len(all_paths)} file WAV -> chia thành {n_batches} batch (batch-size={args.batch_size}).")

    deadline = (time.time() + args.time_budget_sec) if args.time_budget_sec is not None else None
    if deadline is not None:
        print(f"Ngân sách thời gian: {args.time_budget_sec/3600:.2f}h -- sẽ tự dừng an toàn nếu chạm mốc.")

    batch_out_dirs, stopped_early = run_batches(all_paths, args.config, out_root, args.batch_size, deadline)
    result = merge(batch_out_dirs, args.config, out_root)
    if isinstance(result, dict):
        result["partial_run_stopped_early"] = stopped_early
        result["n_batches_done"] = len(batch_out_dirs)
        result["n_batches_target"] = n_batches
        (out_root / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=True))

    if stopped_early:
        print(f"\nLƯU Ý: dừng sớm theo ngân sách thời gian -- summary.json hiện tại"
              f" chỉ phản ánh {len(batch_out_dirs)}/{n_batches} batch. Chạy lại"
              f" lệnh này (không đổi tham số) ở phiên sau để tiếp tục phần còn lại.")


if __name__ == "__main__":
    main()