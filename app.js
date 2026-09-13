import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
const $=s=>document.querySelector(s);
let replay=null, plan=null, time=0, playing=false, local=false, requestSerial=0;
const viewport=$('#viewport');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,2)); renderer.setClearColor(0xe9eee5); renderer.shadowMap.enabled=true;
viewport.prepend(renderer.domElement); renderer.domElement.setAttribute('aria-label','Interactive 3D replay of recorded robot motion');
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(38,1,.005,30); camera.up.set(0,0,1);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=.08;controls.maxDistance=3;
scene.add(new THREE.HemisphereLight(0xffffff,0x86907a,2.7));
const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(1,-1,2);scene.add(light);
const grid=new THREE.GridHelper(1.6,32,0xb8c9aa,0xd3ddcc);grid.rotation.x=Math.PI/2;grid.position.z=-.008;scene.add(grid);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(2,2),new THREE.MeshStandardMaterial({color:0xe9eee5,roughness:1}));floor.position.z=-.011;scene.add(floor);
const group=new THREE.Group();scene.add(group);
let nodeObjects=Object.create(null), visuals=Object.create(null), bars=Object.create(null), trace=null, robotAsset=null;
const assetReady=fetch('assets/so101.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>{robotAsset=d;}).catch(()=>{});
const metallic=new THREE.MeshStandardMaterial({color:0x647d6c,metalness:.35,roughness:.4});
const targetMat=new THREE.MeshStandardMaterial({color:0xdf803e,roughness:.5});
function resize(){const r=viewport.getBoundingClientRect();renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();}
new ResizeObserver(resize).observe(viewport);
function cameraPreset(name){
 const pose=replay?.frames.find(f=>f.poses.target)?.poses.target;
 const target=new THREE.Vector3(...(pose?pose.slice(0,3):[.15,0,.18]));
 const offset={overview:[.45,-.62,.42],gripper:[.26,-.35,.22],top:[0,-.001,.85]}[name]||[.45,-.62,.42];
 if(name==='overview')target.set(.14,.03,.17);
 camera.position.copy(target).add(new THREE.Vector3(...offset));controls.target.copy(target);controls.update();
 document.querySelectorAll('[data-camera]').forEach(b=>b.classList.toggle('selected',b.dataset.camera===name));
}
document.querySelectorAll('[data-camera]').forEach(b=>b.onclick=()=>cameraPreset(b.dataset.camera));
function resetScene(){
 group.traverse(o=>{if(o.geometry)o.geometry.dispose();if(o.material&&o.material!==metallic&&o.material!==targetMat)o.material.dispose();});group.clear();nodeObjects=Object.create(null);visuals=Object.create(null);bars=Object.create(null);
 const profile=replay.visual_profile==='so101'?robotAsset:null;
 $('#geometry-label').textContent=profile?'SO-101 display meshes. Recorded simulation motion; no new physics.':'Schematic robot links. Recorded motion; no new physics.';
 for(const n of replay.nodes){const o=new THREE.Group();o.name=n.id;nodeObjects[n.id]=o;}
 for(const n of replay.nodes){
  const o=nodeObjects[n.id];(n.parent?nodeObjects[n.parent]:group).add(o);
  let visual;
  if(n.kind==='observation')visual=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(n.size,n.size,n.size)),new THREE.LineBasicMaterial({color:0x149e9a}));
  else if(n.kind==='object')visual=new THREE.Mesh(new THREE.BoxGeometry(n.size,n.size,n.size),targetMat);
  else if(profile){
   visual=new THREE.Group();
   for(const p of profile.parts.filter(p=>p.node===n.id)){
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(p.positions,3));geometry.setIndex(p.triangles);geometry.computeVertexNormals();
    const mat=new THREE.MeshStandardMaterial({color:new THREE.Color(...p.color),metalness:.18,roughness:.5});
    visual.add(new THREE.Mesh(geometry,mat));
   }
  } else visual=new THREE.Mesh(new THREE.SphereGeometry(n.size,18,12),metallic);
  o.add(visual);visuals[n.id]=visual;
  if(n.kind==='joint'&&n.parent&&!profile){const bar=new THREE.Mesh(new THREE.CylinderGeometry(.009,.009,1,12),metallic);group.add(bar);bars[n.id]=bar;}
 }
 // Target trajectory is broken at missing samples. Never draw a bridge across a gap.
 const positions=[];
 for(let i=1;i<replay.frames.length;i++){
  const a=replay.frames[i-1].poses.target,b=replay.frames[i].poses.target;
  if(a&&b)positions.push(...a.slice(0,3),...b.slice(0,3));
 }
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
 trace=new THREE.LineSegments(geometry,new THREE.LineBasicMaterial({color:0x90aa81,transparent:true,opacity:.45}));group.add(trace);
 cameraPreset('overview');
}
function validPackage(d){
 if(d?.schema!=='edgegrasp-replay/1'||!Array.isArray(d.nodes)||!Array.isArray(d.frames)||d.frames.length<2||d.frames.length>18000||d.nodes.length>128)throw Error('Unsupported replay package. Use the local converter or a bundled sample.');
 const ids=new Set(d.nodes.map(n=>n.id));if(ids.size!==d.nodes.length)throw Error('Duplicate nodes');
 if(!d.nodes.length||typeof d.title!=='string'||d.title.length>120||!['recorded-simulation','recorded-hardware','synthetic'].includes(d.capture)||![undefined,'so101'].includes(d.visual_profile))throw Error('Invalid replay metadata');
 for(const n of d.nodes){if(typeof n.id!=='string'||!(/^[A-Za-z0-9_-]{1,80}$/).test(n.id)||!['joint','object','observation','anchor'].includes(n.kind)||!Number.isFinite(n.size)||n.size<=0||n.size>10)throw Error('Invalid node');}
 const map=Object.fromEntries(d.nodes.map(n=>[n.id,n]));
 for(const n of d.nodes){let seen=new Set(),v=n;while(v){if(seen.has(v.id))throw Error('Cyclic hierarchy');seen.add(v.id);if(v.parent&&!map[v.parent])throw Error('Missing parent');v=map[v.parent];}}
 let last=-1;for(const f of d.frames){if(!Number.isFinite(f.t)||f.t<=last||f.t>600)throw Error('Invalid time');last=f.t;for(const id of ids){const p=f.poses?.[id];if(p!==null&&(!Array.isArray(p)||p.length!==7||!p.every(Number.isFinite)||p.slice(0,3).some(v=>Math.abs(v)>10000)||Math.abs(p.slice(3).reduce((sum,v)=>sum+v*v,0)-1)>.002))throw Error('Invalid pose');}}
 if(d.frames[0].t!==0||!Array.isArray(d.events))throw Error('Invalid timeline');
 if(d.events.length>500||new Set(d.events.map(e=>e.id)).size!==d.events.length||d.events.some(e=>!(/^event-\d+$/).test(e.id)||!Number.isFinite(e.t)||e.t<0||e.t>last||typeof e.label!=='string'||typeof e.reason!=='string'||e.label.length>500||e.reason.length>500))throw Error('Invalid events');
 return d;
}
function template(d){return {schema:'edgegrasp-shots/1',replay_sha256:d.content_sha256,author:'template',shots:[{start:0,end:d.frames.at(-1).t,camera:'overview',speed:1,event_ids:[]}]};}
function checkPlan(){
 if(plan.replay_sha256!==replay.content_sha256||!plan.shots.length||plan.shots.length>8)throw Error('Shot plan does not match this recording.');
 for(const s of plan.shots){
  if(!Number.isFinite(s.start)||!Number.isFinite(s.end)||s.start<0||s.start>=s.end||s.end>replay.frames.at(-1).t)throw Error('Set each shot inside the recording, with OUT after IN.');
  if(!['overview','gripper','top'].includes(s.camera)||![.25,.5,1,2].includes(s.speed))throw Error('Unsupported camera or speed.');
  if(!Array.isArray(s.event_ids)||s.event_ids.some(id=>!replay.events.some(e=>e.id===id&&e.t>=s.start&&e.t<=s.end)))throw Error('Event citation outside its shot.');
 }
}
function setReplay(d){
 replay=validPackage(d);plan=template(replay);time=0;playing=false;$('#play').textContent='▶';
 $('#replay-title').textContent=replay.title;$('#capture').textContent=replay.capture.toUpperCase();$('#scrub').max=replay.frames.at(-1).t;
 $('#evidence-content').textContent=JSON.stringify({capture:replay.capture,content_sha256:replay.content_sha256,evidence:replay.evidence},null,2);
 resetScene();renderEvents();renderShots();$('#loading').style.display='none';$('#message').textContent='';updateFrame();
}
async function loadSample(id){
 const serial=++requestSerial;$('#loading').textContent='Loading source-bound replay…';$('#loading').style.display='grid';
 try{await assetReady;const response=await fetch(`samples/${id}.json`);if(!response.ok)throw Error('Sample unavailable');const d=await response.json();if(serial!==requestSerial)return;setReplay(d);document.querySelectorAll('[data-sample]').forEach(b=>b.classList.toggle('active',b.dataset.sample===id));}
 catch(e){$('#loading').textContent=e.message;}
}
document.querySelectorAll('[data-sample]').forEach(b=>b.onclick=()=>loadSample(b.dataset.sample));
$('#file').onchange=async e=>{const f=e.target.files[0];if(!f)return;if(f.size>16_000_000)return say('File exceeds 16 MB');try{requestSerial++;setReplay(JSON.parse(await f.text()));document.querySelectorAll('[data-sample]').forEach(b=>b.classList.remove('active'));}catch(err){say(err.message);}};
function frameIndex(t){let lo=0,hi=replay.frames.length-1;while(lo<hi){const mid=Math.ceil((lo+hi)/2);if(replay.frames[mid].t<=t)lo=mid;else hi=mid-1;}return lo;}
function visible(id,f){if(f.poses[id]===null)return false;const n=replay.nodes.find(n=>n.id===id);return !n.parent||visible(n.parent,f);}
function updateFrame(){
 if(!replay)return;const idx=frameIndex(time),f=replay.frames[idx];
 for(const n of replay.nodes){const o=nodeObjects[n.id],p=f.poses[n.id];o.visible=visible(n.id,f);if(p){o.position.set(...p.slice(0,3));o.quaternion.set(p[4],p[5],p[6],p[3]);}visuals[n.id].visible=n.kind==='observation'?$('#perception').checked:n.kind==='object'?$('#target').checked:true;}
 group.updateMatrixWorld(true);
 for(const [id,bar] of Object.entries(bars)){
  const o=nodeObjects[id],a=o.parent.getWorldPosition(new THREE.Vector3()),b=o.getWorldPosition(new THREE.Vector3()),delta=b.clone().sub(a);
  bar.visible=visible(id,f)&&delta.length()>1e-7;bar.position.copy(a).add(b).multiplyScalar(.5);bar.scale.set(1,delta.length(),1);bar.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());
 }
 trace.visible=$('#path').checked;
 $('#time').textContent=`${time.toFixed(2)} / ${replay.frames.at(-1).t.toFixed(2)} s`;$('#scrub').value=time;
 $('#frame-label').textContent=`FRAME ${String(idx+1).padStart(4,'0')} / ${replay.frames.length}`;
 const ev=replay.events.filter(e=>e.t<=time).at(-1);$('#current-event').textContent=ev?ev.label:'BEFORE FIRST RECORDED EVENT';
 $('#contact').textContent=f.contact?`CONTACT ${f.contact.fixed?'L ●':'L ○'} ${f.contact.moving?'R ●':'R ○'}`:'CONTACT UNAVAILABLE';
 document.querySelectorAll('.event').forEach(b=>b.classList.toggle('active',b.dataset.id===ev?.id));
}
function renderEvents(){
 const container=$('#events');container.replaceChildren();$('#event-count').textContent=String(replay.events.length).padStart(2,'0');
 for(const e of replay.events){const b=document.createElement('button');b.className='event';b.dataset.id=e.id;
  const t=document.createElement('span'),label=document.createElement('strong'),reason=document.createElement('small');
  t.textContent=`${e.t.toFixed(2)}s`;label.textContent=e.label.replaceAll('_',' ');reason.textContent=e.reason;
  b.append(t,label,reason);b.onclick=()=>{time=e.t;playing=false;$('#play').textContent='▶';updateFrame();};container.append(b);
 }
}
$('#play').onclick=()=>{if(!replay)return;if(time>=replay.frames.at(-1).t)time=0;playing=!playing;$('#play').textContent=playing?'Ⅱ':'▶';};
$('#scrub').oninput=e=>{time=Number(e.target.value);playing=false;$('#play').textContent='▶';updateFrame();};
for(const id of ['perception','target','path'])$('#'+id).onchange=updateFrame;
$('#evidence-button').onclick=()=>$('#evidence').showModal();
function say(message){$('#message').textContent=message;}
function renderShots(){
 const container=$('#shots');container.replaceChildren();$('#plan-author').textContent=plan.author==='gpt-6-astra'?'ASTRA DRAFT · REVIEW BEFORE EXPORT':'MANUAL / TEMPLATE';
 plan.shots.forEach((shot,i)=>{
  const row=document.createElement('div');row.className='shot';const number=document.createElement('span');number.textContent=String(i+1).padStart(2,'0');row.append(number);
  for(const [field,label] of [['start','IN / SEC'],['end','OUT / SEC'],['camera','CAMERA'],['speed','SPEED']]){
   const wrap=document.createElement('label');wrap.textContent=label;const input=document.createElement(field==='camera'||field==='speed'?'select':'input');
   if(input.tagName==='SELECT'){for(const value of field==='camera'?['overview','gripper','top']:[.25,.5,1,2]){const o=document.createElement('option');o.value=value;o.textContent=String(value);input.append(o);}}
   else{input.type='number';input.min=0;input.max=replay.frames.at(-1).t;input.step=.01;}
   input.value=shot[field];input.setAttribute('aria-label',`Shot ${i+1} ${field}`);
   input.oninput=input.onchange=()=>{shot[field]=field==='camera'?input.value:Number(input.value);shot.event_ids=[];plan.author='user';$('#plan-author').textContent='USER EDITED';};wrap.append(input);row.append(wrap);
  }
  const remove=document.createElement('button');remove.textContent='×';remove.setAttribute('aria-label',`Remove shot ${i+1}`);remove.disabled=plan.shots.length===1;remove.onclick=()=>{plan.shots.splice(i,1);plan.author='user';renderShots();};row.append(remove);container.append(row);
 });
}
$('#add-shot').onclick=()=>{if(!replay||plan.shots.length>=8)return;const end=replay.frames.at(-1).t;const start=Math.min(time,end-.05);plan.shots.push({start:Math.max(0,start),end,camera:'gripper',speed:1,event_ids:[]});plan.author='user';renderShots();};
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
$('#export').onclick=async()=>{
 if(!replay)return;const button=$('#export');button.disabled=true;say('');
 try{
  checkPlan();
  if(!local){download(new Blob([JSON.stringify(plan,null,2)],{type:'application/json'}),'shots.json');say('Shot plan saved. Run the local toolkit to export a Blender bundle.');return;}
  const r=await fetch('api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({replay,plan})});
  if(!r.ok)throw Error((await r.json()).error);download(await r.blob(),'edgegrasp-blender-bundle.zip');say('Bundle ready. Extract it and run the included Blender command; it builds and verifies the scene.');
 }catch(e){say(e.message);}finally{button.disabled=false;}
};
$('#ai-plan').onclick=async()=>{
 if(!replay)return;const button=$('#ai-plan'),boundHash=replay.content_sha256;button.disabled=true;say('Astra is drafting shots from the event metadata…');
 try{const r=await fetch('api/plan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({replay,request:$('#prompt').value,confirm_external_request:true})});const result=await r.json();if(!r.ok)throw Error(result.error);if(replay.content_sha256!==boundHash)throw Error('Recording changed; stale plan discarded.');plan=result.plan;renderShots();say('Astra draft validated. Review the shots before exporting.');}
 catch(e){say(e.message);}finally{button.disabled=false;}
};
fetch('api/status').then(async r=>{if(!r.ok)throw Error();const d=await r.json();local=d.mode==='local';$('#ai-state').textContent=d.astra_available?'ASTRA KEY CONFIGURED · EVENT METADATA ONLY':'LOCAL TOOLKIT · SET OPENAI_API_KEY TO ENABLE ASTRA';$('#ai-plan').disabled=!d.astra_available;}).catch(()=>{$('#ai-state').textContent='PUBLIC DEMO · AI AND BLENDER EXPORT RUN IN THE LOCAL TOOLKIT';$('#export').textContent='Download shot plan ↓';});
let previous=performance.now();function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-previous)/1000,.1);previous=now;if(playing&&replay){time=Math.min(time+dt*Number($('#speed').value),replay.frames.at(-1).t);if(time===replay.frames.at(-1).t){playing=false;$('#play').textContent='▶';}updateFrame();}controls.update();renderer.render(scene,camera);}requestAnimationFrame(animate);
loadSample('release-cycle');
