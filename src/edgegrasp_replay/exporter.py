import io
import json
from pathlib import Path
import zipfile
from .model import validate, validate_plan


def make_bundle(replay, plan):
    validate(replay); validate_plan(plan,replay)
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("replay.json",json.dumps(replay,ensure_ascii=False))
        z.writestr("shots.json",json.dumps(plan,indent=2))
        z.writestr("build_scene.py",Path(__file__).with_name("blender_scene.py").read_bytes())
        if replay.get('visual_profile')=='so101':
            for name in ('so101.json','SO101-LICENSE.txt'):
                z.writestr(name,(Path(__file__).parent/'assets'/name).read_bytes())
        z.writestr("README.txt","EdgeGrasp Replay / portable Blender bundle\n\nRequires Blender 4.x. No ROS, add-ons or script auto-run required to view the resulting scene.\n\nBuild, verify and render a preview:\nblender --background --factory-startup --python build_scene.py -- .\n\nAlso render the complete edited film (can take several minutes):\nblender --background --factory-startup --python build_scene.py -- . --render-video\n\nOutputs: replay.blend, preview.png, verification.json; optionally film.mp4.\nSO-101 samples include attributed simplified public visual meshes; other nodes are schematic. Poses and event times come from the package.\nNo new physics is run. AI plans only select cameras, speeds and recorded intervals.\nNull poses are hidden including descendants. Output frames use preceding recorded samples, with no extrapolation.\nVerification concerns displayed transforms, not physics or hardware success.\n")
    return buffer.getvalue()
