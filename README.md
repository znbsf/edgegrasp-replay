# EdgeGrasp Replay

Turn recorded robot experiments into editable Blender replays.

[Try the public demo](https://znbsf.github.io/edgegrasp-replay/) ·
[Download the local toolkit](https://github.com/znbsf/edgegrasp-replay/releases/tag/v0.1.0)

**Early preview, 0.1.0.** Inspect three real simulation recordings in a browser,
jump to recorded events, choose cuts and cameras, and export an editable Blender
scene. The optional GPT-6 Astra planner drafts shot lists from event metadata.

## Run locally

Requires Python 3.11+ and a browser with WebGL. The packaged player needs no
account, API key, ROS installation or robot connection.

On Windows, double-click `RUN_REPLAY.cmd`, then open http://127.0.0.1:4319.
From a terminal at the project root:

```powershell
$env:PYTHONPATH='src'
python -m edgegrasp_replay.cli serve
```

On macOS/Linux, use `PYTHONPATH=src python -m edgegrasp_replay.cli serve`.
These operating systems have not been tested. Start from the extracted folder;
do not open `index.html` directly with a file URL.

## Make a Blender scene

Choose a recording and edit the shot list. Download and extract the Blender
bundle. In its folder, run your installed Blender executable:

```text
blender --background --factory-startup --python-exit-code 1 --python build_scene.py -- .
```

This writes `replay.blend`, `preview.png` and `verification.json`. Open the
scene in Blender to edit geometry, cameras, lighting and materials. Add
`--render-video` after the final `.` to render the complete edited film.
No Python auto-run is required when opening the saved scene.

The three samples preserve different recorded outcomes: place/release/retreat,
a verified grasp followed by failed release, and a stop before gripper closure.
Sample outcomes are historical records, not conclusions inferred from animation.

## Optional Astra planning

Set `OPENAI_API_KEY` in the server environment and restart the local server.
Do not put your key in the website, a public hosting environment or this repository.
Clicking **Plan with Astra** makes one Responses API call to `gpt-6-astra`.
Only event metadata, duration and your request are sent; pose arrays stay local.
API charges can apply. There are no automatic calls or retries.

The model selects recorded intervals, camera presets and speeds. Deterministic
code validates the plan against the recording hash and builds the scene.
It does not execute generated Python, infer new events or change trajectories.
**The live API path has not yet been validated with an API key.** Mocked tests
verify request scope and rejection behavior; they are not proof of a live run.

## Scope

- Input: portable `edgegrasp-replay/1` JSON or an existing EdgeGrasp replay export.
- Output: a self-contained Blender builder, baked scene and verification receipt.
- SO-101 visuals use attributed, simplified public meshes. Other node hierarchies
  use schematic links. Raw arbitrary URDF, MCAP and Gazebo worlds need an adapter.
- Source exports may already contain display interpolation. The source brackets
  and interpolation disclosure are retained; editing does not add new precision.
- Missing poses hide the affected geometry and descendants. No new physics,
  robot controls or hardware verification occurs.

See [the schema](docs/FORMAT.md), [validation](docs/VALIDATION.md),
[source and license notices](THIRD_PARTY_NOTICES.md) and
[launch preparation](docs/launch/PRODUCT_HUNT.md).

## 中文说明

这是从 EdgeGrasp 回放能力独立出来的展示工具。主项目在本机开发，`.38` 只作为
原始记录来源和独立 Blender 验证环境。用户打开网页就能看记录、定位事件、调整镜头；
需要导出可编辑工程时，在本地用 Blender 生成场景。

它适合实验演示、技术报告和复盘视频；目前不承担新物理仿真、控制真实机器人或自动
判断实验成功。公开网站只能提供回放和镜头计划下载，完整场景导出由本地工具完成。

## Development

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
node --check web/app.js
python scripts/package_release.py
```

The test suite uses Node for a real Python → browser JSON serialization check.
Runtime browser dependencies are vendored. To refresh them: `npm ci --ignore-scripts`
and `npm run vendor`. Private original recordings and output scenes are ignored.
Source code is MIT; third-party mesh and library licenses remain separate.
