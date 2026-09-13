# Validation — 2026-09-13

This is a functional early preview, not proof of hardware or physics correctness.

## Automated checks

19 tests pass with `PYTHONPATH=src python -m unittest discover -s tests -v`:
sample validation, modified-content detection, real Node JSON serialization,
hierarchy cycles/missing parents, missing pose retention, invalid timing and
quaternions, stale plans, event citations, fixed-script bundle contents, local
HTTP exports, cross-origin/Host rejection and private-directory isolation.

Planner tests mock Responses API replies to verify metadata-only input, one-call
behavior, receipt fields, and refusal of invalid/incomplete plans. **These are
not live OpenAI API tests.** No API key was available during this validation.
`node --check web/app.js` also passes.

## Blender round trips

All cases build a scene, save it, reopen it with script auto-run disabled, then
check every output local position, quaternion and visibility against the input.
Parent gaps hide descendants; the synthetic case exercises this explicitly.

| Case | Blender | Output frames | Checked non-null poses | Result |
|---|---|---:|---:|---|
| Place/release/retreat | 4.5.13 LTS | 972 | 9,720 | Pass |
| Stop before closure | 4.5.13 LTS | 495 | 4,950 | Pass |
| Synthetic two-node parent gap | 4.5.13 LTS | 30 | 51 | Pass |
| Four-shot recorded film | 4.5.13 LTS | 285 | 2,850 | Pass |
| Four-shot recorded film, final lighting | 4.1.1 | 285 | 2,850 | Pass |

The `.38` machine ran Blender 4.5.13 in an independent output directory. The
current development machine ran Blender 4.1.1. Original research worktrees and
recordings were read-only. No simulator, controller or hardware experiment ran.

Receipts are under `docs/validation/*.json`. Reported local-position error was
zero for these samples (they were already representable at Blender precision).
Quaternion and visibility assertions passed. These checks do not independently
prove world-frame calibration, mesh collision accuracy, physical success,
source authenticity or long-term reliability. Visual origins for all 17 SO-101
parts matched the pinned public URDF against the source replay URDF.

## Browser and visual checks

Codex in-app browser, desktop viewport and 390×844 mobile override:

- Three.js model renders; sample switching and event jumps work.
- Manual interval and speed edits export a ZIP through the actual browser flow.
- A Python/JavaScript numeric-hash mismatch found in that flow was repaired and
  covered by the Node round-trip regression test.
- Mobile page stays within the viewport; the experiment strip scrolls separately.
- No captured browser warning/error logs after the final model checks.
- Actual screenshots are in `docs/launch/media/` and `docs/validation/mobile.png`.
- A 285-frame / 30 fps Workbench film was rendered from the verified edited scene.
- Static-demo tests reject an out-of-range interval and download a valid plan.
  Numeric fields now synchronize on input, avoiding stale values on immediate export.
- H.264 playback crashed the in-app browser during testing. The website now uses
  WebM with a poster and no preload. Actual WebM playback reported 960×640,
  9.5 seconds, readyState 4, an advancing clock and no media error. MP4 remains
  available as a file; its playback in this in-app browser is not claimed to work.

## Remaining limits

- Live Astra request, model access and quota are unverified.
- Raw arbitrary MCAP/URDF import and additional simulator adapters are not built.
- Static hosting supports replay and shot-plan download; it cannot run Blender
  or the local-only AI endpoint. The downloadable toolkit provides those routes.
- No public API service, authentication system or multi-user backend is provided.
- macOS/Linux, Safari and physical mobile devices have not been tested.
- Product Hunt launch/contest submission and authenticated eligibility remain pending.
