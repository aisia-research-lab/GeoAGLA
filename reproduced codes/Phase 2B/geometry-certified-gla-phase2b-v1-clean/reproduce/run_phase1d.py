from __future__ import annotations
import subprocess, sys


def main():
    print('=== Phase-1D: unit tests ===')
    subprocess.run([sys.executable,'-m','pytest','-q'],check=True)
    print('\n=== Phase-1D: online dominant-edge diagnostics ===')
    subprocess.run([sys.executable,'-m','experiments.phase1d_online_edge.run'],check=True)
    print('\nPhase-1D complete. See results/phase1d/summary.json')

if __name__=='__main__': main()
