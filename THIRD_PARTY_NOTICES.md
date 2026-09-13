# Sources and notices

## SO-101 display geometry

TheRobotStudio/SO-ARM100, commit `eecbe3e0a9ebb23e25ad7b2759b03884c6660903`.
Source: https://github.com/TheRobotStudio/SO-ARM100/tree/eecbe3e0a9ebb23e25ad7b2759b03884c6660903/Simulation/SO101

The repository's Apache-2.0 license is retained in
`web/assets/SO101-LICENSE.txt` and every SO-101 Blender export.
Original Onshape attribution is in the pinned URDF at the source link above.
No upstream endorsement is implied.

Modified visual assets: decimated to 12 percent of source triangles, URDF visual
origins baked into link-local vertices, serialized as JSON. Collision, inertial
and control data are excluded. Each input URL and SHA-256 is retained in
`web/assets/so101.json`. Scripts `fetch_so101.py` and `build_so101.py` reproduce
the conversion. The 17 original replay visual origins were compared with the
pinned public URDF and matched; this does not establish collision accuracy.

## Three.js

Three.js 0.180.0, MIT; license at `web/vendor/THREE-LICENSE.txt`.
https://github.com/mrdoob/three.js/tree/r180
The module builds and OrbitControls are copied without modification.

## EdgeGrasp recordings

The three samples derive from the user's EdgeGrasp simulation replay exports.
MIT source notice: Copyright (c) 2026 EdgeGrasp contributors (see LICENSE).
Public samples remove machine paths and retain a hash of the source export,
recorded timestamps, source brackets and an outcome whitelist.
Original private exports, logs, camera models and Gazebo worlds are not packaged.
Before public release, confirm these experiment records are yours to publish;
no third-party private dataset is intentionally included.

## Trademarks

Blender, OpenAI and Product Hunt identify compatible software or the intended
launch destination. This project does not claim sponsorship or certification.
