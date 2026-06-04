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

Origin is vehicle center on the ground plane.

## Spec → 3D pipeline

1. Edit `config/bucephalus_v0.yaml` (wheelbase, bay IML, tank liters, mass lines).
2. `python -m bucephalus … --export-scene viewer/public/scene.json`
3. `bucephalus/scene.py` derives layout:
   - Body length ≈ `1.72 × wheelbase`, width from track
   - Engine bay aft of center; tunnel/underfloor/seat-back anchors from wheelbase fractions
   - Tank **cylinders** from liter volume (type IV–ish aspect ratios)
   - V10 **schematic**: wireframe envelope + crankcase + two bank boxes + valve cover
4. Viewer reads JSON (boxes + cylinders). Gates unchanged — still from Python math.

Tune anchors in `layout_from_spec()` when clay/CAD gives real positions; later add optional `layout:` overrides in YAML.

## Next step: real CAD

Export glTF from CAD and load beside procedural blocks (Scenepeek-style loader), or replace primitives once positions are frozen.
