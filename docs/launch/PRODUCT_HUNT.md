# Product Hunt preparation — draft, not submitted

Prepared 2026-09-13. Maker identity placeholder: **znbsf**.
Product Hunt account: not yet confirmed/created. This file is editable launch copy.

## Product name

EdgeGrasp Replay

## Tagline

Turn robot recordings into editable Blender replays

## Description

Make robot experiments easier to explain. Inspect recorded motion in your browser, jump to success or failure events, choose cameras and speeds, then export an editable Blender scene. Three real simulation recordings are included. Optional Astra shot planning uses event metadata; trajectories stay local. An early preview for robotics demos and experiment reviews.

## Maker's first comment — draft

Hi Product Hunt! I'm building EdgeGrasp Replay because a robot log and a polished video often tell very different stories.

I wanted a small workflow between them: open a recording, find the important event, choose how to show it, and keep the result editable in Blender. The demo includes a complete place/release/retreat cycle, a grasp followed by a failed release, and a run stopped before gripper closure.

The browser plays the recorded motion. The local toolkit builds and verifies the Blender scene. An optional Astra integration drafts camera cuts and speeds from event metadata, while the trajectories remain unchanged.

This is an early preview. It currently accepts a portable replay format and existing EdgeGrasp exports; arbitrary robot logs need an adapter. It does not run new physics or control hardware. The live Astra API integration is still awaiting validation, so the current demo is fully usable with manual shots.

For people who share robotics experiments: which part costs you more time today—finding the moment worth showing, or turning it into a clear animation?

## Gallery / demo

- `media/workspace.png`: actual browser workspace, recorded motion and event list.
- `media/shot-editor.png`: actual shot editor and export workflow.
- `media/blender-preview.png`: actual output rendered from the exported scene.
- `media/thumbnail.png`: square product mark, 240×240.
- `outputs/demo-film.mp4`: locally available recorded-motion edit; not uploaded.

Prefer the browser and Blender images as the first two gallery items. Do not
substitute invented renderings or advertise untested physics. The optional
YouTube demonstration should show 10 seconds of the browser, 10 seconds of
event/shot editing, and 10 seconds opening the Blender result. End with the
supported-format and local-toolkit scope.

## Challenge gate

Official announcement: https://community.openai.com/t/gpt-6-astra-challenge-on-product-hunt/1396727
Contest: https://www.producthunt.com/contests/gpt-6-astra-challenge
Launch preparation: https://www.producthunt.com/launch/preparing-for-launch

The announcement says launch by September 18, 2026. Exact cutoff timezone,
eligibility for a standalone product derived from older research, residency
requirements and final entry terms remain unverified behind the entry flow.
The public countdown is not treated as an authoritative closing signal.

Prepared for the Astra challenge. Confirm the development session's model evidence
before making a built-with-Astra eligibility claim. A live call to the optional
in-product planner remains unverified.
Do not replace the planner's manual demonstration with a mocked “live AI” clip.

## Remaining actions

1. Register/sign in to Product Hunt and verify the maker profile. The user handles
   any new password, email verification and account terms.
2. Read the current contest terms in the authenticated entry flow; establish
   eligibility and exact deadline before submitting.
3. If the entry requires live in-product Astra use, configure a local API key and
   record a real request receipt, reviewed shots and exported scene.
4. Enter the final public product URL, upload gallery and thumbnail, review the
   listing and schedule/submit according to the current Product Hunt interface.
5. Record the resulting launch/entry URL. No entry is complete without that receipt.

Product Hunt is a product discovery and launch community, not an application
hosting service. A normal launch and admission to this challenge are separate.

## Published product assets

Public demo: https://znbsf.github.io/edgegrasp-replay/
Source: https://github.com/znbsf/edgegrasp-replay
Download: https://github.com/znbsf/edgegrasp-replay/releases/tag/v0.1.0
These are product artifacts; they are not a Product Hunt listing or contest entry.
