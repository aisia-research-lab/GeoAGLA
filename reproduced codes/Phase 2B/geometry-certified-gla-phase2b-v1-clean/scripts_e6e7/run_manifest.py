#!/usr/bin/env python3
import argparse, subprocess, tempfile, shlex
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--adapter',required=True); ap.add_argument('--out',required=True); a=ap.parse_args()
m=load_json(a.manifest); ad=load_json(a.adapter); root=Path(ad['repo_root']); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
for case in m['cases']:
 cd=out/case['case_id']; cd.mkdir(exist_ok=True); cj=cd/'case.json'; dump_json(case,cj)
 cmd=ad['command_template'].format(case_json=str(cj),out_dir=str(cd));
 with open(cd/'command.txt','w') as f:f.write(cmd+'\n')
 p=subprocess.run(cmd,shell=True,cwd=root,text=True,capture_output=True); (cd/'stdout.log').write_text(p.stdout); (cd/'stderr.log').write_text(p.stderr)
 dump_json({'returncode':p.returncode},cd/'runner_status.json')
 if p.returncode: print('FAILED',case['case_id'])
