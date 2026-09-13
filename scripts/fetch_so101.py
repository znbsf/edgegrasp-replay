"""Fetch pinned public SO-101 visual sources. Never reads private machine models."""
import hashlib
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
COMMIT='eecbe3e0a9ebb23e25ad7b2759b03884c6660903'
BASE=f'https://raw.githubusercontent.com/TheRobotStudio/SO-ARM100/{COMMIT}/'
DEST=ROOT/'.local/so101-source'
DEST.mkdir(parents=True,exist_ok=True)
def fetch(remote,local):
    path=DEST/local
    path.parent.mkdir(parents=True,exist_ok=True)
    raw=urllib.request.urlopen(BASE+remote,timeout=60).read()
    path.write_bytes(raw)
    return {'file':local,'url':BASE+remote,'sha256':hashlib.sha256(raw).hexdigest()}
records=[fetch('LICENSE','LICENSE.txt'),fetch('Simulation/SO101/so101_new_calib.urdf','robot.urdf')]
robot=ET.parse(DEST/'robot.urdf')
names=sorted({m.get('filename') for m in robot.findall('.//visual/geometry/mesh')})
for name in names:
    records.append(fetch('Simulation/SO101/'+name,name))
    print(name,flush=True)
(DEST/'sources.json').write_text(json.dumps({'repository':'TheRobotStudio/SO-ARM100','commit':COMMIT,'files':records},indent=2))
