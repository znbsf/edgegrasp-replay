# Replay adapter contract

`edgegrasp-replay/1` is an early, versioned interchange format. The validator
in `src/edgegrasp_replay/model.py` is authoritative. Lengths are metres;
quaternions use **wxyz**. Poses are local to the declared parent. A root pose
is in world coordinates. Frame times are seconds relative to the recording start.

Required package fields: schema, title, capture, fps, nodes, frames, events and
content_sha256. Capture is recorded-simulation, recorded-hardware or synthetic.
The bundled samples are recorded-simulation. `visual_profile: "so101"` opts into
the included public SO-101 display model; omit it for schematic generic nodes.

Each node has a unique id, a parent id or null, kind (joint/object/observation/anchor)
and visual size. Every frame explicitly includes every node's pose or null:

```json
{"t":0,"source_ns":"1000000000000000000","poses":{"root":[0,0,0,1,0,0,0],"child":null}}
```

Nanoseconds are strings to avoid JavaScript integer precision loss. Null is a
missing measurement and hides the node and descendants; it is never a zero pose.
Frame times must strictly increase from zero. Limits: ten minutes, 18,000 frames,
128 nodes, 500 events. Browser/API requests are limited to 16 MB.

Events have unique event-N ids, a recorded t, label and reason. Shot citations
must name events inside the shot interval. A shot plan uses edgegrasp-shots/1,
the input replay_sha256, author (template/user/gpt-6-astra), and 1–8 shots with
start/end seconds, camera (overview/gripper/top), speed (0.25/0.5/1/2), event_ids.

`content_sha256` hashes all fields except itself using a typed recursive JSON
representation and normalized binary64 numbers. Use `seal()` from the Python
package; ordinary json.dumps SHA-256 is not this format's hash. The hash detects
accidental changes and stale plans. It is not a digital signature or proof that
the original recording is authentic.

To support another simulator, write an adapter which emits this hierarchy,
explicit null gaps, local poses, source timestamps and recorded events. Preserve
interpolation disclosure. Do not label generated frames recorded-hardware.
The test fixture in `scripts/prepare_validation.py` illustrates a separate two-node
hierarchy; it is synthetic, not a second simulator integration.
