# Agent Instructions

Your task is to **recreate** the campus in SketchUp from scratch.

**Do not repair the supplied SKP.**

Read `README.md` completely before doing any modeling.

## Non-negotiable rule

The source model under `input/` is **read-only reference material**.

You MUST:

1. inspect the source model and the images under `references/`;
2. create a brand-new blank SketchUp file;
3. rebuild the campus in that new file;
4. save only the newly recreated model as your submission.

You MUST NOT:

- edit the source SKP;
- clean or repair its geometry;
- Save As from the source model;
- copy the whole source model into a new file;
- copy individual source buildings, bridges, platforms, or terrain into the final model;
- use the old model's broken internal topology as the basis of the submission.

The benchmark tests whether you can understand the reference and independently reconstruct it.

## What must be reproduced

Recreate as faithfully as practical:

- major campus buildings;
- building footprints, massing, height, orientation, and relative placement;
- bridges;
- inter-building platforms;
- roads and plazas;
- important terrain / elevation relationships;
- stadium and major sports areas;
- other structures that materially affect campus topology.

The campus contains complex bridges, platforms, and terrain. Do not omit difficult structures simply because they are difficult to model.

## Structure of the new model

Prefer clean semantic Groups / Components, such as:

`Terrain / Roads / Platforms / Bridges / Buildings / Sports / Other`

Buildings, bridges, platforms, and terrain should be independently selectable where practical.

Do not create unnecessary fragmented groups.

## Reference priority

When references disagree slightly:

1. use the source SKP for 3D height, bridge, platform, slope, and spatial-connection information;
2. use the aerial image to verify footprints and overall layout;
3. use the zoning image only for campus extent and functional-area identification.

## Required deliverable

The PR must add:

`submissions/<agent-name>/campus_recreated.blend`

The `.blend` file is the primary submission for the current benchmark. If the environment can reliably export SketchUp, the PR may additionally include:

`submissions/<agent-name>/campus_recreated.skp`

A repaired model named `campus_repaired.blend` or `campus_repaired.skp` is **not** a valid submission for the current benchmark.

Screenshots, renders, reports, OBJ, FBX, STL, or scripts do not replace the required BLEND.

## GitHub workflow

Do not commit the submission directly to `main`.

Create a branch and open a Pull Request.

PR title:

`[Submission] <agent-name> - campus reconstruction`

In the PR description, identify the Agent/model used, Blender version and main tools, reconstructed content, and known deviations. Explicitly confirm that the final model was created as a new reconstruction from the locked reference and was not produced by repairing, cleaning, or saving a copy of the source SKP.
