from __future__ import annotations
import json, subprocess, sys
from pathlib import Path


def run_module(module):
    print(f"\n=== {module} ===")
    subprocess.run([sys.executable,"-m",module],check=True)


def main():
    subprocess.run([sys.executable,"-m","pytest","-q"],check=True)
    run_module("experiments.s0_linear.run")
    run_module("experiments.h1_geometry.run")
    run_module("experiments.h2_oracle_rate.run")
    print("\nPhase-1B reproduction completed. See results/phase1b/*.json")

if __name__=="__main__": main()
