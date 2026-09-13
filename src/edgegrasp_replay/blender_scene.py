"""Self-contained Blender 4.x script. Data is JSON; no generated code is evaluated."""
import bisect
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector, Quaternion

args=sys.argv[sys.argv.index('--')+1:]
root=Path(args[0]).resolve()
data=json.loads((root/'replay.json').read_text(encoding='utf-8'))
plan=json.loads((root/'shots.json').read_text(encoding='utf-8'))
def canonical(value):
    if value is None: return ['null']
    if isinstance(value,bool): return ['bool',value]
    if isinstance(value,(int,float)):
        assert math.isfinite(value)
        return ['number',float(value).hex() if value != 0 else '0x0.0p+0']
    if isinstance(value,str): return ['string',value]
    if isinstance(value,list): return ['array',[canonical(v) for v in value]]
    if isinstance(value,dict): return ['object',[[k,canonical(v)] for k,v in sorted(value.items())]]
    raise ValueError('Non-JSON value')
actual=hashlib.sha256(json.dumps(canonical({k:v for k,v in data.items() if k!='content_sha256'}),separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
assert actual==data['content_sha256']==plan['replay_sha256'], 'Input/plan hash mismatch'
assert data['schema']=='edgegrasp-replay/1' and plan['schema']=='edgegrasp-shots/1'
assert 2<=len(data['frames'])<=18000 and 1<=len(data['nodes'])<=128
assert 1<=len(plan['shots'])<=8
for shot in plan['shots']:
    assert 0<=shot['start']<shot['end']<=data['frames'][-1]['t']
    assert shot['speed'] in (.25,.5,1,2) and shot['camera'] in ('overview','gripper','top')

scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE_NEXT' if bpy.app.version>=(4,2,0) else 'BLENDER_EEVEE'
scene.render.resolution_x=960; scene.render.resolution_y=640; scene.render.resolution_percentage=100
scene.render.fps=30
scene.world.color=(.045,.045,.055)
scene.view_settings.view_transform='AgX'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def material(name, color, emission=False):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bsdf=m.node_tree.nodes.get('Principled BSDF'); bsdf.inputs['Base Color'].default_value=(*color,1)
    bsdf.inputs['Metallic'].default_value=.35; bsdf.inputs['Roughness'].default_value=.4
    if emission:
        bsdf.inputs['Emission Color'].default_value=(*color,1); bsdf.inputs['Emission Strength'].default_value=.5
    return m

silver=material('Ceramic / schematic links',(.62,.69,.76)); orange=material('Recorded target',(.96,.24,.075))
cyan=material('Measured pose',(.1,.9,.85),True); dark=material('Stage',(.07,.085,.11))
objects={}; visuals={}; links={}
profile=json.loads((root/'so101.json').read_text()) if data.get('visual_profile')=='so101' else None
profile_nodes={p['node'] for p in profile['parts']} if profile else set()
for n in data['nodes']:
    o=bpy.data.objects.new(n['id'],None); scene.collection.objects.link(o); o.rotation_mode='QUATERNION'; objects[n['id']]=o
for n in data['nodes']:
    o=objects[n['id']]
    if n['parent']: o.parent=objects[n['parent']]
    if n['kind'] in ('object','observation'):
        bpy.ops.mesh.primitive_cube_add(size=n['size']); v=bpy.context.object
        if n['kind']=='observation':
            mod=v.modifiers.new('Wire','WIREFRAME'); mod.thickness=.0013
        v.data.materials.append(cyan if n['kind']=='observation' else orange)
    elif n['id'] in profile_nodes or (profile and n['id']=='gripper_frame_link'):
        v=bpy.data.objects.new('mesh-group',None);scene.collection.objects.link(v)
        for index,part in enumerate(profile['parts']):
            if part['node']!=n['id']: continue
            coords=part['positions']; indices=part['triangles']
            mesh=bpy.data.meshes.new('SO101 visual')
            mesh.from_pydata([coords[i:i+3] for i in range(0,len(coords),3)],[],[indices[i:i+3] for i in range(0,len(indices),3)])
            mesh.update()
            child=bpy.data.objects.new('SO101/'+str(index),mesh);scene.collection.objects.link(child);child.parent=v
            child.data.materials.append(material('SO101/'+str(index),part['color']))
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=n['size']); v=bpy.context.object; v.data.materials.append(silver)
    v.name='visual/'+n['id']; v.parent=o; visuals[n['id']]=v
    if n['kind']=='joint' and n['parent'] and not profile:
        bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.009,depth=1)
        bar=bpy.context.object; bar.name='link/'+n['id']; bar.data.materials.append(silver); links[n['id']]=bar

# Scene props are schematic and fixed; recorded geometry is never used as physics.
bpy.ops.mesh.primitive_cube_add(size=1,location=(.22,.08,-.025))
table=bpy.context.object; table.name='Schematic stage'; table.scale=(.85,.65,.03); table.data.materials.append(dark)
target=next((f['poses'].get('target') for f in data['frames'] if f['poses'].get('target')),None)
focus=Vector(target[:3] if target else (.15,0,.18))
for loc,power,size in [((1,-1,2),70,3),((-1,1,1),45,2),((0,0,2),35,2)]:
    bpy.ops.object.light_add(type='AREA',location=loc); l=bpy.context.object; l.data.energy=power; l.data.shape='DISK'; l.data.size=size

cams={}
for name,offset,scale in [('overview',(.75,-1.05,.7),.85),('gripper',(.35,-.48,.25),.3),('top',(0,-.001,1.4),.72)]:
    bpy.ops.object.camera_add(location=focus+Vector(offset)); c=bpy.context.object; c.name=name
    c.rotation_euler=(focus-c.location).to_track_quat('-Z','Y').to_euler(); c.data.type='ORTHO'; c.data.ortho_scale=scale; c.data.lens=45; cams[name]=c

times=[f['t'] for f in data['frames']]; samples=[]
for shot in plan['shots']:
    count=max(1,math.ceil((shot['end']-shot['start'])*30/shot['speed']))
    assert len(samples)+count<=72000, 'Edited film too long'
    marker=scene.timeline_markers.new(shot['camera'],frame=len(samples)+1); marker.camera=cams[shot['camera']]
    for j in range(count):
        t=min(shot['end'],shot['start']+j*shot['speed']/30)
        samples.append(max(0,bisect.bisect_right(times,t)-1))
scene.camera=cams[plan['shots'][0]['camera']]

def effective_visible(node_id, frame):
    if frame['poses'][node_id] is None: return False
    parent=objects[node_id].parent
    return parent is None or effective_visible(parent.name,frame)

for frame_num,idx in enumerate(samples,1):
    f=data['frames'][idx]; scene.frame_set(frame_num)
    for node_id,o in objects.items():
        pose=f['poses'][node_id]
        if pose is not None:
            o.location=pose[:3]; o.rotation_quaternion=pose[3:]
            o.keyframe_insert('location',frame=frame_num); o.keyframe_insert('rotation_quaternion',frame=frame_num)
        v=visuals[node_id]; v.hide_render=v.hide_viewport=not effective_visible(node_id,f)
        v.keyframe_insert('hide_render',frame=frame_num); v.keyframe_insert('hide_viewport',frame=frame_num)
        for child in v.children:
            child.hide_render=child.hide_viewport=v.hide_render
            child.keyframe_insert('hide_render',frame=frame_num);child.keyframe_insert('hide_viewport',frame=frame_num)
    bpy.context.view_layer.update()
    for node_id,bar in links.items():
        o=objects[node_id]; a=o.parent.matrix_world.translation; b=o.matrix_world.translation; delta=b-a
        bar.location=(a+b)/2; bar.rotation_mode='QUATERNION'; bar.rotation_quaternion=delta.to_track_quat('Z','Y') if delta.length>1e-8 else Quaternion()
        bar.scale=(1,1,max(delta.length,1e-8)); bar.hide_render=bar.hide_viewport=not effective_visible(node_id,f)
        for prop in ('location','rotation_quaternion','scale','hide_render','hide_viewport'): bar.keyframe_insert(prop,frame=frame_num)
for event in data['events']:
    for output_i,source_i in enumerate(samples):
        if data['frames'][source_i]['t']>=event['t'] and (output_i==0 or data['frames'][samples[output_i-1]]['t']<event['t']):
            scene.timeline_markers.new(event['label'][:60],frame=output_i+1)
scene.frame_start=1; scene.frame_end=len(samples)
scene['capture']=data['capture']; scene['source_sha256']=actual; scene['physics_recomputed']=False
scene['recorded_evidence']=json.dumps(data.get('evidence',{})); scene['plan_author']=plan['author']
text=bpy.data.texts.new('SOURCE_AND_SHOTS.json'); text.write(json.dumps({'replay_sha256':actual,'plan':plan,'output_source_indices':samples,'events':data['events']},indent=2))
scene.frame_set(max(1,len(samples)//2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'replay.blend'))
# Reopen and verify every output sample against the exact input pose and visibility.
bpy.ops.wm.open_mainfile(filepath=str(root/'replay.blend'),use_scripts=False)
scene=bpy.context.scene; objects={n['id']:bpy.data.objects[n['id']] for n in data['nodes']}
max_error=0.; checked=0
for frame_num,idx in enumerate(samples,1):
    scene.frame_set(frame_num); f=data['frames'][idx]
    for node_id,o in objects.items():
        pose=f['poses'][node_id]
        assert bpy.data.objects['visual/'+node_id].hide_render == (not effective_visible(node_id,f))
        for child in bpy.data.objects['visual/'+node_id].children:
            assert child.hide_render == (not effective_visible(node_id,f))
        if pose is not None:
            err=(o.location-Vector(pose[:3])).length; max_error=max(max_error,err)
            assert err<1e-5
            angle=o.rotation_quaternion.rotation_difference(Quaternion(pose[3:])).angle
            assert min(angle,abs(2*math.pi-angle))<.002
            checked+=1
assert not scene.rigidbody_world
receipt={'passed':True,'claim':'display_transform_and_visibility_roundtrip_only','source_sha256':actual,
         'output_frames':len(samples),'checked_poses':checked,'max_position_error_m':max_error,
         'physics_recomputed':False,'hardware_verified':False,'blender_version':bpy.app.version_string}
(root/'verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
scene.frame_set(max(1,len(samples)//2)); scene.render.image_settings.file_format='PNG'; scene.render.filepath=str(root/'preview.png')
bpy.ops.render.render(write_still=True)
if '--render-video' in args:
    scene.render.image_settings.file_format='FFMPEG'; scene.render.ffmpeg.format='MPEG4'; scene.render.ffmpeg.codec='H264'
    scene.render.filepath=str(root/'film.mp4'); bpy.ops.render.render(animation=True)
print(json.dumps(receipt))
