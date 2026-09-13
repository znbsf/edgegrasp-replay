"""Loopback UI, validated downloads and optional explicit Astra requests."""
import functools
import json
import os
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from .model import validate, validate_plan
from .exporter import make_bundle
from .planner import plan_with_astra


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cache-Control','no-store')
        super().end_headers()

    def reply(self,status,body,mime='application/json'):
        raw=body if isinstance(body,bytes) else json.dumps(body).encode()
        self.send_response(status); self.send_header('Content-Type',mime); self.send_header('Content-Length',str(len(raw)))
        self.end_headers(); self.wfile.write(raw)

    def allowed(self):
        expected=f'127.0.0.1:{self.server.server_port}'
        if self.headers.get('Host')!=expected: return False
        origin=self.headers.get('Origin')
        return not origin or origin=='http://'+expected

    def do_GET(self):
        if not self.allowed(): return self.reply(403,{'error':'Local origin required'})
        if self.path=='/api/status':
            return self.reply(200,{'mode':'local','astra_available':bool(os.environ.get('OPENAI_API_KEY')),'model':'gpt-6-astra'})
        return super().do_GET()

    def do_POST(self):
        if not self.allowed(): return self.reply(403,{'error':'Local origin required'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=16_000_000: raise ValueError('Request exceeds 16 MB limit')
            body=json.loads(self.rfile.read(length)); replay=validate(body['replay'])
            if self.path=='/api/export':
                plan=validate_plan(body['plan'],replay)
                return self.reply(200,make_bundle(replay,plan),'application/zip')
            if self.path=='/api/plan':
                if body.get('confirm_external_request') is not True: raise ValueError('Explicit AI request required')
                return self.reply(200,plan_with_astra(replay,body['request']))
            return self.reply(404,{'error':'Unknown action'})
        except (ValueError,KeyError,TypeError) as exc:
            self.reply(400,{'error':str(exc)[:240]})
        except Exception:
            # Never reflect provider payloads, local paths or credentials to the client.
            self.reply(502,{'error':'Request failed. No plan applied; check local configuration and provider access.'})


def serve(webroot, port=4319):
    server=ThreadingHTTPServer(('127.0.0.1',port),functools.partial(Handler,directory=str(webroot)))
    print(f'EdgeGrasp Replay http://127.0.0.1:{port}',flush=True)
    server.serve_forever()
