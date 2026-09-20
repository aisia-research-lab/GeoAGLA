#!/usr/bin/env python3
import argparse
from pathlib import Path
from common import *
ap=argparse.ArgumentParser(); ap.add_argument('--e6-summary',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); s=load_json(a.e6_summary); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
rows=[['Metric','Value'],['N cases',s.get('n_cases')],['Median oracle opportunity',s['oracle_opportunity']['median']],['Median online gain',s['online_gain']['median']],['Median capture',s['capture']['median']],['Capture >= 0.5',s['capture']['frac_ge_0p5'],],['Pearson gain correlation',s['correlation']['pearson']],['Spearman gain correlation',s['correlation']['spearman']]]
with open(out/'table_e6_summary.tex','w') as f:
 f.write('\\begin{tabular}{lr}\n\\toprule\nMetric & Value \\\\\n\\midrule\n')
 for k,v in rows[1:]: f.write(f'{k} & {v} \\\\\n')
 f.write('\\bottomrule\n\\end{tabular}\n')
write_csv([{'metric':k,'value':v} for k,v in rows[1:]],out/'table_e6_summary.csv')
