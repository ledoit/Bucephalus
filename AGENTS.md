# Bucephalus — Agent guide

## Scope

Packaging, H2 storage mass, mass budget, and feasibility gates only. Do not add CFD, FEA, or engine simulation unless the user explicitly expands scope.

## Conventions

- Numbers in `config/*.yaml` are user-owned; presets in `references.py` must cite approximate public sources in `note`.
- Keep hydrogen model honest: order-of-magnitude density, not homologation.
- CLI exit `1` on gate failure is intentional.
- Tests must run without network.

## Commands

```bash
pip install -e .
python -m bucephalus config/bucephalus_v0.yaml
python -m bucephalus moodboard list
python -m bucephalus moodboard optimize --write-spec config/bucephalus_optimized.yaml
python -m bucephalus moodboard blend-mesh --use-optimized
streamlit run bucephalus/ui/app.py
pytest
```

Mood board: `config/moodboard.yaml` (user weights) + `config/catalog.yaml` (reference coeffs; optional GLB in `meshes/`). Interpolation is coefficient-space weighted blending, not vertex morphing.

*Last updated: 2026-05-25*
