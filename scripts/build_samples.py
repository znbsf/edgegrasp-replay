"""Rebuild sanitized public samples from explicitly selected local source exports."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from edgegrasp_replay.adapter import convert

for name,title in [('release-cycle','Place, release, retreat'),('grasp-release-failed','Grasp verified, release failed'),('safe-stop','Stopped before gripper closure')]:
    data=convert(ROOT/f'.local/source/{name}.json',title)
    (ROOT/f'web/samples/{name}.json').write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
    print(name,data['content_sha256'])
