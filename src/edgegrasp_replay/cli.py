import argparse
import json
from pathlib import Path
from .model import validate, default_plan
from .adapter import convert
from .exporter import make_bundle


def main():
    p=argparse.ArgumentParser(description='EdgeGrasp Replay: offline robot experiment films')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('serve'); s.add_argument('--web',type=Path,default=Path('web')); s.add_argument('--port',type=int,default=4319)
    s=sub.add_parser('convert'); s.add_argument('source',type=Path); s.add_argument('output',type=Path); s.add_argument('--title',required=True)
    s=sub.add_parser('validate'); s.add_argument('source',type=Path)
    s=sub.add_parser('export'); s.add_argument('source',type=Path); s.add_argument('output',type=Path); s.add_argument('--plan',type=Path)
    args=p.parse_args()
    if args.command=='serve':
        from .server import serve
        return serve(args.web.resolve(),args.port)
    if args.command=='convert':
        data=convert(args.source,args.title)
        with args.output.open('x',encoding='utf-8') as out: json.dump(data,out,separators=(',',':'),ensure_ascii=False)
        print(data['content_sha256']); return
    data=validate(json.loads(args.source.read_text(encoding='utf-8')))
    if args.command=='validate': print(json.dumps({'valid':True,'frames':len(data['frames']),'sha256':data['content_sha256']})); return
    plan=json.loads(args.plan.read_text()) if args.plan else default_plan(data)
    with args.output.open('xb') as out: out.write(make_bundle(data,plan))
    print(args.output)

if __name__=='__main__': main()
