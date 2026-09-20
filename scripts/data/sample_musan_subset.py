#!/usr/bin/env python3
"""
sample_musan_subset.py
======================
Stratified sampling script for the MUSAN audio dataset.
Used for real-audio basin transfer evaluations (Phase 2B / E5b).

Features:
- Traverses subdirectories of the source audio corpus (speech, music, noise).
- Performs stratified random sampling with a fixed random seed (default: 42) for 100% reproducibility.
- Preserves directory hierarchy and root metadata (README, LICENSE).
- Generates `subset_manifest.tsv` with relative paths and byte sizes.
- Optional compression to a `.zip` archive.

Usage:
    # 25% subsample:
    python scripts/data/sample_musan_subset.py \
        --src-root /path/to/musan \
        --dst-root data/musan_25 \
        --ratio 0.25 --seed 42 --zip-path data/musan_25.zip

    # 10% subsample:
    python scripts/data/sample_musan_subset.py \
        --src-root /path/to/musan \
        --dst-root data/musan_10 \
        --ratio 0.10 --seed 42
"""
from __future__ import annotations

import argparse
import os
import random
import shutil
import zipfile
from pathlib import Path
from typing import List, Tuple, Set


def sample_audio_subset(
    src_root: Path | str,
    dst_root: Path | str,
    ratio: float = 0.25,
    seed: int = 42,
    zip_path: Path | str | None = None,
    audio_exts: Set[str] | None = None,
    copy_meta: bool = True,
) -> Tuple[int, int, Path]:
    src_root = Path(src_root).resolve()
    dst_root = Path(dst_root).resolve()
    if audio_exts is None:
        audio_exts = {".wav"}

    if not src_root.exists():
        raise FileNotFoundError(f"Source directory not found: {src_root}")

    rng = random.Random(seed)
    dst_root.mkdir(parents=True, exist_ok=True)

    manifest: List[Tuple[str, int]] = []
    n_total = 0
    n_kept = 0

    print(f"Sampling from {src_root} to {dst_root} (ratio={ratio:.2f}, seed={seed})...")

    for dirpath_str, _, filenames in os.walk(src_root):
        dirpath = Path(dirpath_str)
        rel_dir = dirpath.relative_to(src_root)

        audio_files = sorted(f for f in filenames if Path(f).suffix.lower() in audio_exts)
        if audio_files:
            k = max(1, round(len(audio_files) * ratio))
            chosen = rng.sample(audio_files, k)
            (dst_root / rel_dir).mkdir(parents=True, exist_ok=True)

            for fname in sorted(chosen):
                src_file = dirpath / fname
                dst_file = dst_root / rel_dir / fname
                shutil.copyfile(src_file, dst_file)
                manifest.append((str(rel_dir / fname), dst_file.stat().st_size))

            n_total += len(audio_files)
            n_kept += len(chosen)

        if copy_meta and rel_dir == Path("."):
            for f in filenames:
                if Path(f).suffix.lower() not in audio_exts:
                    shutil.copyfile(dirpath / f, dst_root / f)

    manifest_path = dst_root / "subset_manifest.tsv"
    with open(manifest_path, "w", encoding="utf-8") as fh:
        fh.write(f"# seed={seed} ratio={ratio}\n")
        fh.write("# relative_path\tsize_bytes\n")
        for rel, size in sorted(manifest):
            fh.write(f"{rel}\t{size}\n")

    percent = (n_kept / max(n_total, 1)) * 100
    print(f"Sampled {n_kept}/{n_total} audio files ({percent:.2f}%).")
    print(f"Manifest written to: {manifest_path}")

    if zip_path:
        zip_p = Path(zip_path).resolve()
        if zip_p.exists():
            zip_p.unlink()
        zip_p.parent.mkdir(parents=True, exist_ok=True)
        print(f"Creating zip archive: {zip_p}...")
        with zipfile.ZipFile(zip_p, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
            for f in sorted(dst_root.rglob("*")):
                if f.is_file():
                    zf.write(f, arcname=dst_root.name / f.relative_to(dst_root))
        size_gb = zip_p.stat().st_size / 1e9
        print(f"Archive created: {zip_p} ({size_gb:.2f} GB)")

    return n_kept, n_total, dst_root


def main():
    parser = argparse.ArgumentParser(
        description="Stratified sampling of the MUSAN audio dataset for Phase-2B experiments."
    )
    parser.add_argument("--src-root", required=True, help="Path to source MUSAN directory.")
    parser.add_argument("--dst-root", required=True, help="Path to destination subset directory.")
    parser.add_argument("--ratio", type=float, default=0.25, help="Subsampling ratio (default: 0.25).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42).")
    parser.add_argument("--zip-path", type=str, default=None, help="Optional destination path for zip archive.")
    parser.add_argument("--no-copy-meta", action="store_true", help="Do not copy metadata files (README, LICENSE) at root.")
    args = parser.parse_args()

    sample_audio_subset(
        src_root=args.src_root,
        dst_root=args.dst_root,
        ratio=args.ratio,
        seed=args.seed,
        zip_path=args.zip_path,
        copy_meta=not args.no_copy_meta,
    )


if __name__ == "__main__":
    main()
