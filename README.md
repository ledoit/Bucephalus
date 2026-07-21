# Bucephalus

Feasibility math for a **transverse-mounted V10 hydrogen combustion** car with **no trunk and no frunk**. This does not design engines, tanks, or crash structures — it tells you early whether your claimed numbers fit together.

**Last reviewed:** 2026-05-25

## What it actually does

| Module | Reality check |
|--------|----------------|
| `packaging` | Transverse bay fit: crank span vs lateral limit, bank depth vs fore-aft, height stack |
| `hydrogen` | 700 bar bulk H2 mass from tank geometry (NIST-order density, not certification) |
| `mass_budget` | Sum your YAML mass lines + engine; rough CG |
| `gates` | PASS/FAIL on bay, storage slack, curb mass, range target |

## What it does **not** do

- CFD, combustion, knock, or emissions homologation
- Tank burst, permeation, or GTR / FMVSS sign-off
- Suspension kinematics or tire model
- Replace CAD — export numbers **into** CAD as hard constraints

## Quick start

```bash
cd Menhir/Bucephalus
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt pytest
python -m bucephalus config/bucephalus_v0.yaml
pytest
```

Exit code `0` = all gates pass; `1` = at least one NO-GO (expected until you tune `config/bucephalus_v0.yaml` to measured packaging).

## Edit your concept

`config/bucephalus_v0.yaml` — wheelbase, bay IML, tank volumes in tunnel/underfloor/seat-back only, mass lines. Engine presets live in `bucephalus/references.py`:

- `lamborghini_5.2_v10_reference` — compact V10 envelope baseline
- `ford_6.8_v10_truck_reference` — sanity check for “wrong V10”

## Next real-world steps (outside this repo)

1. Measure engine bay IML from clay/CAD → update `bay.*`
2. Tank vendor datasheet → update `storage.tanks` and `mass_lines.h2_tanks_dry`
3. Weigh subsystems on scales → replace placeholder `mass_lines`
4. Export gate failures as dimensioned constraints for your CAD team

## Menhir location

`Menhir/Bucephalus` — standalone Python; init git here when you want version control.


## License

All Rights Reserved © Menhir Holdings
