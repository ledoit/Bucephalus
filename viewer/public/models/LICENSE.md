# Reference vehicle shell

## `sports_shell.glb`

- **Source:** [three.js examples](https://github.com/mrdoob/three.js/tree/r128/examples/models/gltf) — Ferrari 458–style reference mesh (Draco-compressed).
- **Use in Bucephalus:** Scaled to your YAML wheelbase/body length as a **packaging reference**, not a product design or trademark asset.
- **Replace:** Drop your own measured glTF/GLB as `custom_shell.glb` or use **Replace shell…** in the viewer.

## Your CAD

Preferred path for production review:

1. Export clay/CAD as `.glb` (meters or mm — viewer fits to `target_length_mm` in `scene.json`).
2. Place at `viewer/public/models/custom_shell.glb` and set `vehicle_shell.url` in exported JSON, or upload in the browser.
