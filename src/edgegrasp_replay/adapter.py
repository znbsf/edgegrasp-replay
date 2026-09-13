"""EdgeGrasp source adapter. Does not copy private paths or third-party meshes."""
import hashlib
import json
import math
from pathlib import Path
from .model import seal


def quaternion(rows):
    # Stable matrix -> wxyz conversion; handles rotations near pi.
    m = rows
    t = m[0][0] + m[1][1] + m[2][2]
    if t > 0:
        s = math.sqrt(t+1)*2
        q = [s/4,(m[2][1]-m[1][2])/s,(m[0][2]-m[2][0])/s,(m[1][0]-m[0][1])/s]
    else:
        i = max(range(3), key=lambda k:m[k][k]); j=(i+1)%3; k=(i+2)%3
        s=math.sqrt(1+m[i][i]-m[j][j]-m[k][k])*2
        q=[0,0,0,0]; q[0]=(m[k][j]-m[j][k])/s; q[i+1]=s/4
        q[j+1]=(m[j][i]+m[i][j])/s; q[k+1]=(m[k][i]+m[i][k])/s
    norm=math.sqrt(sum(v*v for v in q))
    return [v/norm for v in q]


def convert(source, title):
    raw=Path(source).read_bytes(); old=json.loads(raw)
    if old.get("schema_version") != 1 or old.get("physics_recomputed") is not False:
        raise ValueError("Expected recorded EdgeGrasp replay schema 1")
    keep=["base_link","shoulder_link","upper_arm_link","lower_arm_link","wrist_link","gripper_link","moving_jaw_so101_v1_link","gripper_frame_link"]
    nodes=[{"id":i,"parent":old["parents"].get(i) if old["parents"].get(i) in keep else None,
            "kind":"joint", "size":0.012 if i != "base_link" else 0.028} for i in keep]
    nodes += [{"id":"target","parent":None,"kind":"object","size":0.05},
              {"id":"perception","parent":"base_link","kind":"observation","size":0.051}]
    first=old["frames"][0]["source_ns"]
    frames=[]
    for f in old["frames"]:
        poses={}
        for i in keep:
            p=old["static"].get(i)
            if i in f["tf"]: p=f["tf"][i][0] if f["tf"][i] else None
            poses[i]=p
        poses["target"]=f["cube"][0] if f.get("cube") else None
        obs=f.get("observation")
        poses["perception"]=obs[1]["center_m"]+quaternion(obs[1]["orientation_rows"]) if obs else None
        frames.append({"t":round((f["source_ns"]-first)/1e9,9),"source_ns":str(f["source_ns"]),
                       "poses":poses,"contact":f.get("contact")[1] if f.get("contact") else None,
                       "source_brackets":{i:v[1] for i,v in f["tf"].items() if i in keep and v}})
    events=[]; seen=set(); omitted=0
    for e in old.get("events",[]):
        t=round((int(e["time_ns"])-first)/1e9,9)
        key=(e.get("phase",""),e.get("reason",""))
        if not 0 <= t <= frames[-1]["t"]: omitted+=1; continue
        if key in seen: continue
        seen.add(key)
        events.append({"id":f"event-{len(events)+1}","t":t,"label":str(e.get("phase") or e.get("event_type") or "Event")[:500],
                       "reason":str(e.get("reason",""))[:500],"time_basis":e.get("time_basis","recorded_log_time")})
    result=old.get("recorded_result",{})
    # Explicit whitelist: aggregate original result, never recompute success from animation.
    keys=("physics_grasp_verified","physics_reason","sequence_completed","sequence_reason","baseline_z_m","final_z_m","retention_observed")
    return seal({"schema":"edgegrasp-replay/1","title":title,"capture":"recorded-simulation","fps":old["fps"],"visual_profile":"so101",
                 "nodes":nodes,"frames":frames,"events":sorted(events,key=lambda e:e["t"]),
                 "evidence":{"source_replay_sha256":hashlib.sha256(raw).hexdigest(),"hardware_verified":False,
                    "geometry":"SO-101 public visual meshes, decimated; no collision model", "out_of_range_events":omitted,
                    "recorded_result":{k:result[k] for k in keys if k in result},
                    "recorded_cycle_status":old.get("recorded_cycle_status"),"typed_release_exit_code":old.get("typed_release_exit_code"),
                    "display_interpolation":old.get("display_interpolation"),"no_new_physics":True}})
