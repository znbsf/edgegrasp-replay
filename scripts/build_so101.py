"""Blender-only offline conversion of pinned SO-101 visuals to compact mesh JSON.
Changes: visual-only geometry, decimation, baked URDF visual offsets, JSON encoding.
TheRobotStudio/SO-ARM100 sources are Apache-2.0; retained license ships with output.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import bpy
from mathutils import Matrix, Euler, Vector

source,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
tree=ET.parse(source/'robot.urdf')
materials={m.get('name'):[float(x) for x in m.find('color').get('rgba').split()][:3] for m in tree.findall('material')}
parts=[]
for link in tree.findall('link'):
    for visual in link.findall('visual'):
        mesh=visual.find('geometry/mesh')
        if mesh is None: continue
        bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
        bpy.ops.wm.stl_import(filepath=str(source/mesh.get('filename')))
        obj=bpy.context.object; obj.data=obj.data.copy()
        modifier=obj.modifiers.new('Display simplification','DECIMATE');modifier.ratio=.12
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        origin=visual.find('origin')
        xyz=[float(x) for x in origin.get('xyz','0 0 0').split()]
        rpy=[float(x) for x in origin.get('rpy','0 0 0').split()]
        transform=Matrix.Translation(Vector(xyz)) @ Euler(rpy,'XYZ').to_matrix().to_4x4()
        obj.data.calc_loop_triangles()
        positions=[round(c,7) for v in obj.data.vertices for c in (transform @ v.co)]
        triangles=[i for tri in obj.data.loop_triangles for i in tri.vertices]
        parts.append({'node':link.get('name'),'color':materials[visual.find('material').get('name')], 'positions':positions,'triangles':triangles})
        print(link.get('name'),len(triangles)//3,flush=True)
result={'schema':'edgegrasp-visuals/1','profile':'so101','license':'Apache-2.0','source':json.loads((source/'sources.json').read_text()),'changes':'Decimated to 12 percent; URDF visual offsets baked into link-local vertices; no collision or physics data.','parts':parts}
(out/'so101.json').write_text(json.dumps(result,separators=(',',':')))
(out/'SO101-LICENSE.txt').write_bytes((source/'LICENSE.txt').read_bytes())
package=Path(__file__).resolve().parents[1]/'src/edgegrasp_replay/assets'
package.mkdir(parents=True,exist_ok=True)
for name in ('so101.json','SO101-LICENSE.txt'):
    (package/name).write_bytes((out/name).read_bytes())
