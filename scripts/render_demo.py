"""Render an already verified edited scene using Blender's Workbench renderer."""
from pathlib import Path
import sys
import bpy
root=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.open_mainfile(filepath=str(root/'replay.blend'),use_scripts=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=960;scene.render.resolution_y=640
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL'
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.background_type='WORLD';scene.world.color=(.08,.1,.12)
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264'
scene.render.filepath=str(root/'demo-film.mp4')
if '--webm' in sys.argv:
    scene.render.ffmpeg.format='WEBM';scene.render.ffmpeg.codec='WEBM'
    scene.render.filepath=str(root/'demo-film.webm')
bpy.ops.render.render(animation=True)
