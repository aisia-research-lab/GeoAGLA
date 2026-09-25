from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def main():
    cmd = [
        sys.executable,
        str(ROOT / "experiments" / "08_e10_robustness_mechanism_ablation" / "11_e10r2f_final_archive.py"),
    ] + sys.argv[1:]
    subprocess.run(cmd, check=True, cwd=str(ROOT))


if __name__ == "__main__":
    main()
