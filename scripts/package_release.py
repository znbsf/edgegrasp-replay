"""Build an allowlisted source toolkit and a self-contained static demo."""
import hashlib
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'dist';out.mkdir(exist_ok=True)
files=[]
for folder in ('src','web','tests','scripts','docs'):
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.blend') and 'downloads' not in p.parts)
for name in ('README.md','LICENSE','THIRD_PARTY_NOTICES.md','pyproject.toml','package.json','package-lock.json','RUN_REPLAY.cmd'):
    files.append(ROOT/name)
def write_zip(path,entries):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,raw in sorted(entries):
            info=zipfile.ZipInfo(name,date_time=(2026,9,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,raw)
toolkit=out/'edgegrasp-replay-0.1.0.zip'
write_zip(toolkit,[(str(p.relative_to(ROOT)).replace('\\','/'),p.read_bytes()) for p in files])
site=out/'site';site.mkdir(exist_ok=True)
for p in (ROOT/'web').rglob('*'):
    if p.is_file():
        target=site/p.relative_to(ROOT/'web');target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
(site/'downloads').mkdir(exist_ok=True)
(site/'downloads'/toolkit.name).write_bytes(toolkit.read_bytes())
(site/'.nojekyll').write_text('')
write_zip(out/'edgegrasp-replay-static-site.zip',[(str(p.relative_to(site)).replace('\\','/'),p.read_bytes()) for p in site.rglob('*') if p.is_file()])
manifest={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (toolkit,out/'edgegrasp-replay-static-site.zip')}
(out/'SHA256.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
