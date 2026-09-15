# Agent Instructions

Your task is to repair the supplied SketchUp campus model.

Read `README.md` before editing the model.

## Required workflow

1. Start from the source model under `input/`.
2. Repair the model while preserving the original appearance, world-space placement, dimensions, materials, terrain, platforms, bridges, and building relationships.
3. Prefer separating mixed raw geometry into meaningful Groups / Components rather than rebuilding the campus from scratch.
4. When uncertain whether geometry is erroneous or intentional, preserve it.
5. Do not commit directly to `main`.
6. Create a branch and open a Pull Request.

## Required deliverable

The PR **must contain a repaired SketchUp file** at:

`submissions/<agent-name>/campus_repaired.skp`

A PR without the repaired `.skp` file is incomplete.

Do not substitute screenshots, renders, OBJ, FBX, STL, reports, or instructions for the required SKP file.

## PR title

`[Submission] <agent-name> - campus repair`

Use the pull request template and state any unresolved problems honestly.
