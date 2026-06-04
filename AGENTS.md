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
pip install -r requirements.txt pytest
python -m bucephalus config/bucephalus_v0.yaml
python -m bucephalus config/bucephalus_v0.yaml --export-scene viewer/public/scene.json
cd viewer && npm install && npm run dev
pytest
```

Scene layout lives in `bucephalus/scene.py` (block primitives only). Do not claim CAD accuracy in the viewer — update YAML and re-export JSON when bay IML or tank positions are measured.

*Last updated: 2026-05-25*
