from __future__ import annotations
import subprocess,sys

def run(cmd):
    print('\n$',' '.join(cmd),flush=True); subprocess.run(cmd,check=True)

def main():
    run([sys.executable,'-m','pytest','-q'])
    run([sys.executable,'-m','experiments.phase1e_safeguarded.run'])
if __name__=='__main__': main()
