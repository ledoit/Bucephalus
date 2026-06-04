# Getting a real car model in and out of Bucephalus

Bucephalus is not a CAD modeler. It **checks YAML math** (mass, bay fit, H₂, gates) and **reviews packaging** on a glTF shell. The procedural boxes were never meant to look like a final car.

## What each overlay means

| Layer | Meaning |
|-------|---------|
| **Car shell** | External glB (reference coupe or your CAD) |
| **Bay IML** | Max engine bay box from `config/*.yaml` |
| **V10 fit box** | Transverse engine + clearances vs bay |
| **H₂ tanks** | Cylinders sized from liter spec — tunnel = spine, underfloor = aft flat pack |
| **CG** | **Center of gravity** — weighted average of `mass_lines` + engine (not aesthetic) |
| **Axle lines** | Wheel centerlines at YAML `wheelbase_mm` (lateral cylinders) |

When the shell loads, overlays **re-seat** on the body (engine bay rear-mid, tanks in tunnel/underfloor regions). Without a shell, positions are rough spec math only — that is why it felt random.

## Recommended AI → Bucephalus loop

### 1. Generate or capture a base mesh

Pick one path:

| Tool | Best for | Output |
|------|----------|--------|
| **[Meshy](https://www.meshy.ai/)** | Text/image → vehicle-ish mesh | GLB export |
| **[Tripo](https://www.tripo3d.ai/)** | Fast concept models | GLB |
| **[Rodin (Hyper3D)](https://hyper3d.ai/)** | Higher-detail concepts | GLB |
| **Blender + CAD blockout** | Measured packaging you trust | GLB export |
| **Photogrammetry** | Real car scan (heavy cleanup) | GLB via Blender |

Prompt tips: *mid-engine sports coupe, no rear trunk volume, flat underfloor, 2480mm wheelbase proportion* — then **scale in Blender** to your measured wheelbase.

### 2. Bring GLB into Bucephalus

**Fast path (browser):**

1. `python -m bucephalus config/bucephalus_v0.yaml --export-scene viewer/public/scene.json`
2. Open viewer → **Replace shell (glb)…**
3. Toggle layers; adjust YAML; re-export JSON.

**Repo path (Vercel / team):**

```bash
cp my_car.glb viewer/public/models/custom_shell.glb
# Edit exported scene.json vehicle_shell.url → models/custom_shell.glb
# Or add a small script to patch JSON after export
```

### 3. Close the loop back to Python gates

AI mesh does **not** update feasibility math. You still:

1. Measure bay IML, tank volumes, masses in the real world or Blender.
2. Edit `config/bucephalus_v0.yaml`.
3. Run `python -m bucephalus config/bucephalus_v0.yaml` for gates.
4. Re-export `scene.json` for the viewer.

Optional automation (later):

```bash
# Example CI sketch
python -m bucephalus config/bucephalus_v0.yaml --export-scene viewer/public/scene.json
cd viewer && npm run build
```

## Routing through an external AI agent

If you want a dedicated “build the car” agent:

1. **Input bundle** you send it:
   - `config/bucephalus_v0.yaml`
   - `viewer/public/scene.json` (packaging anchors)
   - Gate report markdown from CLI
   - Reference photos / orthographic sketches

2. **Ask it to deliver:**
   - `custom_shell.glb` (mm or meters, Z-up, centered near origin)
   - Optional: updated `layout` fractions for tanks/bay once measured in Blender

3. **Drop artifacts back:**
   - GLB → `viewer/public/models/custom_shell.glb`
   - Re-export scene JSON or patch `vehicle_shell.url`
   - Commit + Vercel redeploy

Cursor / Claude / GPT with **3D plugins** (Meshy API, Blender MCP if you run Blender locally) fit this handoff; Bucephalus stays the **feasibility + review** hub.

## What we are not doing (yet)

- Live CAD parametric sync (Fusion/Blender drivers)
- Automatic tank placement from mesh boolean (needs measured anchors in YAML)
- Homologation or crash modeling

Those belong in CAD + simulation; Bucephalus remains the early **numbers + packaging sanity** layer.
