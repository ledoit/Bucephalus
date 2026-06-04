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
4. Viewer loads **`vehicle_shell`** glTF (scaled to `target_length_mm`) plus overlay primitives.
5. Gates unchanged — still from Python math.

## Using your own car model

1. Export clay/CAD as **GLB** (Blender: File → Export → glTF, format GLB).
2. In the viewer: **Replace shell (glb)…** — packaging overlays stay aligned to the same JSON anchors.
3. Or commit `viewer/public/models/custom_shell.glb` and set in YAML export / `scene.json`:
   ```json
   "vehicle_shell": { "url": "/models/custom_shell.glb", "target_length_mm": 4260, ... }
   ```
4. Tune `rotation_deg` / `offset_mm` in exported JSON if the model imports sideways.

Tune packaging anchors in `layout_from_spec()` when measured; optional future `layout:` block in YAML.
