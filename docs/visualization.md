# Visualization

Bucephalus math stays in Python; the **viewer** is a read-only Three.js preview of exported block geometry.

## Workflow

1. Edit `config/bucephalus_v0.yaml` (bay, tanks, mass lines).
2. Export scene JSON:
   ```bash
   python -m bucephalus config/bucephalus_v0.yaml --export-scene viewer/public/scene.json
   ```
3. Run the viewer:
   ```bash
   cd viewer && npm install && npm run dev
   ```

## Coordinate system

| Axis | Direction |
|------|-----------|
| X | Fore-aft (positive = forward) |
| Y | Lateral (positive = left) |
| Z | Up from ground |

Origin is vehicle center on the ground plane. Block positions in `bucephalus/scene.py` are **tentative** until you align them to CAD.

## What is modeled

- Body shell (rough envelope from wheelbase + track)
- Engine bay IML box from `bay.*`
- Transverse engine envelope from preset or custom `engine.*`
- Packaging voids (tunnel / underfloor / seat-back volumes)
- Tank boxes sized from liter volumes
- Mass-budget CG marker
- Gate pass/fail in the side panel

## Next step: real CAD

When you have a glTF/GLB from CAD, you can load it in the viewer the same way Scenepeek loads assets — add a loader hook beside the JSON blocks, or replace blocks once positions are frozen.
