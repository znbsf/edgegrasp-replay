import functools
import http.client
import io
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from edgegrasp_replay.server import Handler
from edgegrasp_replay.model import default_plan
from edgegrasp_replay.planner import plan_with_astra

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'web/samples/safe-stop.json').read_text())
class SilentHandler(Handler):
    def log_message(self,*args):pass

class ServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(SilentHandler,directory=str(ROOT/'web')))
        cls.worker=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.worker.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.worker.join()
    def request(self,body,origin=None,host=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        headers={'Content-Type':'application/json'}
        if origin:headers['Origin']=origin
        if host:headers['Host']=host
        conn.request('POST','/api/export',json.dumps(body),headers)
        response=conn.getresponse();result=response.status,response.read();conn.close();return result
    def test_actual_http_export_and_cross_origin_rejection(self):
        body={'replay':DATA,'plan':default_plan(DATA)}
        status,raw=self.request(body);self.assertEqual(status,200);self.assertTrue(raw.startswith(b'PK'))
        self.assertEqual(self.request(body,origin='https://example.com')[0],403)
        self.assertEqual(self.request(body,host='evil.example')[0],403)
    def test_invalid_plan_does_not_export(self):
        p=default_plan(DATA);p['shots'][0]['end']=10000
        self.assertEqual(self.request({'replay':DATA,'plan':p})[0],400)
    def test_no_source_directory_is_served(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        conn.request('GET','/../.local/source/robot.urdf')
        self.assertEqual(conn.getresponse().status,404);conn.close()

class PlannerContractTests(unittest.TestCase):
    def response(self,shots,status='completed'):
        return io.BytesIO(json.dumps({'id':'mock-response','model':'gpt-6-astra','status':status,'usage':{'output_tokens':10},
            'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'shots':shots})}]}]}).encode())
    def test_mocked_response_metadata_scope_and_receipt(self):
        shots=default_plan(DATA)['shots']
        with patch.dict('os.environ',{'OPENAI_API_KEY':'test-only'}),patch('urllib.request.urlopen',return_value=self.response(shots)) as call:
            result=plan_with_astra(DATA,'Show the refusal')
        self.assertEqual(result['plan']['author'],'gpt-6-astra')
        self.assertEqual(result['receipt']['response_id'],'mock-response')
        payload=json.loads(call.call_args.args[0].data)
        metadata=json.loads(payload['input']);self.assertEqual(set(metadata),{'duration','events','request'})
        self.assertFalse(payload['store']);self.assertEqual(call.call_count,1)
    def test_mocked_invalid_and_incomplete_plans_never_apply(self):
        shots=default_plan(DATA)['shots'];shots[0]['event_ids']=['event-999999']
        for response in (self.response(shots),self.response(shots,'incomplete')):
            with patch.dict('os.environ',{'OPENAI_API_KEY':'test-only'}),patch('urllib.request.urlopen',return_value=response):
                with self.assertRaises(ValueError):plan_with_astra(DATA,'Show the refusal')

if __name__=='__main__':unittest.main()
