#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--audio-dir',required=True); ap.add_argument('--out',required=True); ap.add_argument('--max-files',type=int,default=10); a=ap.parse_args()
fs=sorted(Path(a.audio_dir).rglob('*.wav'))[:a.max_files]
rows=[{'audio_id':f'A{i:03d}','filename':p.name,'relative_path':str(p.relative_to(a.audio_dir)),'sha256':sha256_file(p)} for i,p in enumerate(fs)]
dump_json({'frozen':True,'selection_rule':'alphabetical recursive WAV order','files':rows},a.out); print(sha256_file(a.out))
