"""Portable replay contract. ROS/Blender are not needed to validate it."""
import hashlib
import json
import math
import re


def canonical(value):
    # JSON crosses Python and JavaScript: 1.0 becomes 1, exponent spellings change.
    # Hash typed binary64 values, not the serializer's textual number formatting.
    if value is None: return ["null"]
    if isinstance(value, bool): return ["bool",value]
    if isinstance(value, (int,float)):
        if not math.isfinite(value): raise ValueError("Non-finite number")
        return ["number",float(value).hex() if value != 0 else "0x0.0p+0"]
    if isinstance(value, str): return ["string",value]
    if isinstance(value, list): return ["array",[canonical(v) for v in value]]
    if isinstance(value, dict): return ["object",[[k,canonical(v)] for k,v in sorted(value.items())]]
    raise ValueError("Non-JSON value")


def digest(value):
    return hashlib.sha256(json.dumps(canonical(value), separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate(data):
    if not isinstance(data, dict) or data.get("schema") != "edgegrasp-replay/1":
        raise ValueError("Expected edgegrasp-replay/1 package")
    if data.get("capture") not in ("recorded-simulation", "recorded-hardware", "synthetic"):
        raise ValueError("Capture provenance is required")
    if data.get("visual_profile") not in (None,"so101"):
        raise ValueError("Unsupported visual profile")
    nodes = data.get("nodes", [])
    frames = data.get("frames", [])
    if not 1 <= len(nodes) <= 128 or not 2 <= len(frames) <= 18000:
        raise ValueError("Package requires 1–128 nodes and 2–18000 frames")
    ids = [n.get("id") for n in nodes]
    if any(not isinstance(i, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", i) for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Invalid or duplicate node IDs")
    mapping = {n["id"]: n for n in nodes}
    for n in nodes:
        if n.get("kind") not in ("joint", "object", "observation", "anchor"):
            raise ValueError("Unknown node kind")
        if n.get("parent") is not None and n["parent"] not in mapping:
            raise ValueError("Missing parent")
        if not finite(n.get("size")) or not 0 < n["size"] <= 10:
            raise ValueError("Invalid visual size")
        visited, current = set(), n
        while current:
            if current["id"] in visited:
                raise ValueError("Cyclic transform hierarchy")
            visited.add(current["id"])
            current = mapping.get(current.get("parent"))
    if not finite(data.get("fps")) or not 1 <= data["fps"] <= 120:
        raise ValueError("Invalid FPS")
    last = -1
    for f in frames:
        t = f.get("t")
        if not finite(t) or t < 0 or t <= last:
            raise ValueError("Frame time must be finite and strictly increasing")
        last = t
        if set(f.get("poses", {})) != set(ids):
            raise ValueError("Every frame must explicitly include each pose or null")
        for p in f["poses"].values():
            if p is None:
                continue
            if not isinstance(p, list) or len(p) != 7 or not all(finite(v) for v in p):
                raise ValueError("Pose requires xyz + wxyz quaternion")
            if any(abs(v) > 10000 for v in p[:3]) or abs(sum(v*v for v in p[3:])-1) > 0.002:
                raise ValueError("Invalid position or quaternion")
        if not isinstance(f.get("source_ns"), str) or not f["source_ns"].isdigit():
            raise ValueError("Source time must be an integer nanosecond string")
    if frames[0]["t"] != 0 or last > 600:
        raise ValueError("Replay must start at zero and fit within ten minutes")
    events = data.get("events", [])
    event_ids = [e.get("id") for e in events]
    if len(events) > 500 or len(set(event_ids)) != len(event_ids):
        raise ValueError("Duplicate or excessive events")
    for e in events:
        if not isinstance(e.get("id"), str) or not re.fullmatch(r"event-\d+", e["id"]):
            raise ValueError("Invalid event ID")
        if not finite(e.get("t")) or not 0 <= e["t"] <= last:
            raise ValueError("Event outside recorded range")
        for field in ("label", "reason"):
            if not isinstance(e.get(field), str) or len(e[field]) > 500:
                raise ValueError("Invalid event text")
    if not isinstance(data.get("title"), str) or len(data["title"]) > 120:
        raise ValueError("Invalid title")
    if data.get("content_sha256") != digest({k:v for k,v in data.items() if k != "content_sha256"}):
        raise ValueError("Replay content hash does not match")
    return data


def seal(data):
    data.pop("content_sha256", None)
    data["content_sha256"] = digest(data)
    return validate(data)


def validate_plan(plan, replay):
    validate(replay)
    if plan.get("schema") != "edgegrasp-shots/1" or plan.get("replay_sha256") != replay["content_sha256"]:
        raise ValueError("Shot plan belongs to a different replay")
    if plan.get("author") not in ("template", "user", "gpt-6-astra"):
        raise ValueError("Unknown plan author")
    shots = plan.get("shots", [])
    if not 1 <= len(shots) <= 8:
        raise ValueError("Use 1–8 shots")
    events = {e["id"]:e for e in replay["events"]}
    for shot in shots:
        start, end = shot.get("start"), shot.get("end")
        if not finite(start) or not finite(end) or not 0 <= start < end <= replay["frames"][-1]["t"]:
            raise ValueError("Shot time outside replay")
        if shot.get("camera") not in ("overview", "gripper", "top"):
            raise ValueError("Unsupported camera")
        if not finite(shot.get("speed")) or shot["speed"] not in (0.25, 0.5, 1, 2):
            raise ValueError("Unsupported speed")
        if not isinstance(shot.get("event_ids"), list):
            raise ValueError("Event citations required")
        if any(i not in events or not start <= events[i]["t"] <= end for i in shot["event_ids"]):
            raise ValueError("Shot cites an event outside its interval")
    return plan


def default_plan(replay):
    return {"schema":"edgegrasp-shots/1", "replay_sha256":replay["content_sha256"], "author":"template",
            "shots":[{"start":0, "end":replay["frames"][-1]["t"], "camera":"overview", "speed":1, "event_ids":[]}]}
