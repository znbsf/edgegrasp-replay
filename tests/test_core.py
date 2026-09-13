import copy
import io
import json
import tempfile
import subprocess
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from edgegrasp_replay.model import validate, seal, validate_plan, default_plan
from edgegrasp_replay.exporter import make_bundle
from edgegrasp_replay.planner import plan_with_astra

ROOT=Path(__file__).resolve().parents[1]


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((ROOT/'web/samples/safe-stop.json').read_text())

    def test_all_real_samples_preserve_recorded_scope(self):
        for path in (ROOT/'web/samples').glob('*.json'):
            d=validate(json.loads(path.read_text()))
            self.assertEqual(d['capture'],'recorded-simulation')
            self.assertFalse(d['evidence']['hardware_verified'])
            self.assertTrue(d['evidence']['no_new_physics'])

    def test_modified_pose_cannot_keep_old_hash(self):
        self.data['frames'][0]['poses']['target'][0]+=.1
        with self.assertRaisesRegex(ValueError,'hash'): validate(self.data)

    def test_browser_json_roundtrip_keeps_source_binding(self):
        proc=subprocess.run(['node','-e','let s="";process.stdin.on("data",x=>s+=x);process.stdin.on("end",()=>process.stdout.write(JSON.stringify(JSON.parse(s))))'],input=json.dumps(self.data),text=True,capture_output=True,check=True)
        validate(json.loads(proc.stdout))

    def test_parent_cycle_rejected(self):
        self.data['nodes'][0]['parent']='gripper_link'
        with self.assertRaisesRegex(ValueError,'Cyclic'): seal(self.data)

    def test_missing_parent_rejected(self):
        self.data['nodes'][0]['parent']='unknown'
        with self.assertRaisesRegex(ValueError,'parent'): seal(self.data)

    def test_nan_and_bad_quaternion_rejected(self):
        for pose in [[float('nan'),0,0,1,0,0,0],[0,0,0,0,0,0,0]]:
            d=copy.deepcopy(self.data);d['frames'][0]['poses']['target']=pose
            with self.assertRaises(ValueError): seal(d)

    def test_nonmonotonic_clock_rejected(self):
        self.data['frames'][2]['t']=self.data['frames'][1]['t']
        with self.assertRaisesRegex(ValueError,'increasing'): seal(self.data)

    def test_missing_samples_are_explicit_and_retained(self):
        self.data['frames'][1]['poses']['target']=None
        d=seal(self.data)
        self.assertIsNone(d['frames'][1]['poses']['target'])
        del d['frames'][2]['poses']['target']
        with self.assertRaisesRegex(ValueError,'explicitly'): seal(d)

    def test_changed_input_rejects_old_plan(self):
        p=default_plan(self.data);self.data['title']='new';seal(self.data)
        with self.assertRaisesRegex(ValueError,'different replay'):validate_plan(p,self.data)

    def test_invalid_shot_time_camera_speed_and_citations(self):
        for changes in ({'start':-1},{'end':9999},{'camera':'exec(cmd)'},{'speed':0},{'event_ids':['event-99999']}):
            p=default_plan(self.data);p['shots'][0].update(changes)
            with self.assertRaises(ValueError):validate_plan(p,self.data)

    def test_event_must_be_inside_shot(self):
        event=next(e for e in self.data['events'] if e['t']>1)
        p=default_plan(self.data);p['shots'][0].update(end=.5,event_ids=[event['id']])
        with self.assertRaisesRegex(ValueError,'outside'):validate_plan(p,self.data)

    def test_export_is_data_plus_fixed_script(self):
        raw=make_bundle(self.data,default_plan(self.data))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertEqual(set(z.namelist()),{'replay.json','shots.json','build_scene.py','README.txt','so101.json','SO101-LICENSE.txt'})
            self.assertEqual(json.loads(z.read('replay.json'))['content_sha256'],self.data['content_sha256'])
            self.assertNotIn(b'C:\\Users\\',z.read('replay.json'))
            self.assertEqual(z.read('build_scene.py'),(ROOT/'src/edgegrasp_replay/blender_scene.py').read_bytes())

    def test_missing_api_key_does_not_call_provider(self):
        with patch.dict('os.environ',{},clear=True),patch('urllib.request.urlopen') as call:
            with self.assertRaisesRegex(ValueError,'OPENAI_API_KEY'):plan_with_astra(self.data,'Close up the failure')
            call.assert_not_called()

    def test_public_samples_do_not_include_machine_paths(self):
        for path in (ROOT/'web/samples').glob('*.json'):
            text=path.read_text()
            for bad in ('C:\\','/home/','192.168.','api_key'):
                self.assertNotIn(bad,text)

if __name__=='__main__':unittest.main()
