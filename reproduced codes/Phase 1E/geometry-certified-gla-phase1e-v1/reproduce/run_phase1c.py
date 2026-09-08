from __future__ import annotations
import subprocess, sys


def run(cmd):
    print("\n+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    run([sys.executable, "-m", "pytest", "-q"])
    run([sys.executable, "-m", "experiments.phase1c_multi.run", "--config", "configs/phase1c_grid.json", "--out", "results/phase1c"])
