"""Prepare actual-recording Blender cases and a clearly synthetic gap fixture."""
import json
import sys
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from edgegrasp_replay.model import default_plan, seal
from edgegrasp_replay.exporter import make_bundle
out=ROOT/'.local/validation-v3';out.mkdir(parents=True,exist_ok=True)
for name in ('release-cycle','safe-stop'):
    data=json.loads((ROOT/f'web/samples/{name}.json').read_text())
    (out/f'{name}.zip').write_bytes(make_bundle(data,default_plan(data)))
data=json.loads((ROOT/'web/samples/release-cycle.json').read_text())
plan=default_plan(data);plan['author']='user'
plan['shots']=[dict(start=a,end=b,camera=c,speed=s,event_ids=[]) for a,b,c,s in [(8,13,'overview',2),(13,16,'gripper',1),(22,26,'top',2),(27,31,'overview',2)]]
(out/'demo-film.zip').write_bytes(make_bundle(data,plan))
fixture={'schema':'edgegrasp-replay/1','title':'Synthetic hierarchy gap fixture','capture':'synthetic','fps':10,
    'nodes':[{'id':'root','parent':None,'kind':'joint','size':.03},{'id':'child','parent':'root','kind':'joint','size':.02}],
    'frames':[{'t':i/10,'source_ns':str(i*100000000),'poses':{'root':None if 3<=i<=5 else [i/100,0,0,1,0,0,0],'child':[0,0,.2,1,0,0,0]}} for i in range(11)],'events':[],'evidence':{'synthetic_fixture':True}}
seal(fixture)
(out/'synthetic-gap.zip').write_bytes(make_bundle(fixture,default_plan(fixture)))
print(out)
