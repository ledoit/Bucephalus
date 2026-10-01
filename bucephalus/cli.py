import argparse
import json
import sys
from pathlib import Path

from bucephalus.coefficients import blend_coefficients, coeffs_to_vehicle_spec, pairwise_shortlist
from bucephalus.gates import run_gates
from bucephalus.iterate import rank_shortlist, recursive_refine
from bucephalus.load_spec import load_vehicle_spec
from bucephalus.moodboard import (
    add_moodboard_entry,
    load_moodboard,
    resolve_moodboard_coefficients,
)
from bucephalus.report import format_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = ROOT / "config" / "bucephalus_v0.yaml"


def _cmd_evaluate(args: argparse.Namespace) -> int:
    spec = load_vehicle_spec(args.spec)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    if args.json:
        report = run_gates(spec)
        print(
            json.dumps(
                {
                    "vehicle": spec.name,
                    "passed": report.passed,
                    "gates": [
                        {"id": g.id, "passed": g.passed, "detail": g.detail}
                        for g in report.gates
                    ],
                },
                indent=2,
            )
        )
    else:
        print(format_report(spec))
    return 0 if run_gates(spec).passed else 1


def _cmd_moodboard_list(_: argparse.Namespace) -> int:
    entries = load_moodboard()
    if not entries:
        print("Mood board is empty. Add entries with: bucephalus moodboard add --brand X --model Y")
        return 0
    for i, e in enumerate(entries, 1):
        label = e.slug or f"{e.brand} {e.model}".strip()
        note = f" — {e.note}" if e.note else ""
        print(f"{i}. {label} (weight {e.weight:.2f}){note}")
    return 0


def _cmd_moodboard_add(args: argparse.Namespace) -> int:
    add_moodboard_entry(
        brand=args.brand,
        model=args.model,
        slug=args.slug,
        weight=args.weight,
        note=args.note or "",
    )
    label = args.slug or f"{args.brand} {args.model}".strip()
    print(f"Added {label} (weight {args.weight})")
    return 0


def _cmd_moodboard_extract(args: argparse.Namespace) -> int:
    from bucephalus.catalog import load_catalog, save_catalog
    from bucephalus.mesh_extract import MESHES_DIR, refresh_catalog_from_meshes

    catalog = load_catalog()
    updated = refresh_catalog_from_meshes(catalog, MESHES_DIR)
    save_catalog(updated)
    mesh_hits = [s for s, c in updated.items() if c.mesh_path and "mesh-derived" in c.source_note]
    print(f"Catalog refreshed ({len(catalog)} entries, {len(mesh_hits)} mesh-updated).")
    if not mesh_hits:
        print(f"Drop GLB/OBJ files in {MESHES_DIR} named like catalog slugs (e.g. lamborghini_huracan.glb).")
    return 0


def _cmd_moodboard_shortlist(args: argparse.Namespace) -> int:
    base = load_vehicle_spec(args.base)
    items = resolve_moodboard_coefficients()
    candidates = pairwise_shortlist(items, args.count)
    ranked = rank_shortlist(candidates, base)

    if args.json:
        payload = [
            {
                "slug": c.slug,
                "model": c.model,
                "gates_passed": passed,
                "penalty": round(penalty, 4),
                "coefficients": c.numeric_vector(),
            }
            for c, penalty, passed in ranked
        ]
        print(json.dumps(payload, indent=2))
        return 0

    print(f"# Mood-board shortlist ({len(ranked)} candidates)\n")
    for c, penalty, passed in ranked:
        print(f"## {c.slug} — {passed}/7 gates, penalty {penalty:.3f}")
        v = c.numeric_vector()
        print(
            f"- wheelbase {v['wheelbase_mm']:.0f} mm | bay "
            f"{v['bay_max_lateral_mm']:.0f}×{v['bay_max_fore_aft_mm']:.0f}×"
            f"{v['bay_max_height_mm']:.0f} mm | curb {v['curb_mass_kg']:.0f} kg"
        )
        print()
    return 0


def _cmd_moodboard_optimize(args: argparse.Namespace) -> int:
    from bucephalus.export_spec import write_vehicle_spec_yaml
    from bucephalus.optimize import optimize_weights

    base = load_vehicle_spec(args.base)
    items = resolve_moodboard_coefficients()
    result = optimize_weights(items, base, target_alpha=args.alpha)

    if args.json:
        print(
            json.dumps(
                {
                    "success": result.success,
                    "message": result.message,
                    "penalty": round(result.penalty, 4),
                    "gates_passed": result.gates_passed,
                    "weights": {k: round(v, 4) for k, v in result.weights.items()},
                    "coefficients": result.blended.numeric_vector(),
                },
                indent=2,
            )
        )
    else:
        print(f"# Optimized weights — {result.gates_passed}/7 gates, penalty {result.penalty:.4f}\n")
        for slug, w in sorted(result.weights.items(), key=lambda x: -x[1]):
            print(f"  {slug}: {w:.3f}")
        print()
        print(format_report(result.spec))

    if args.write_spec:
        args.write_spec.parent.mkdir(parents=True, exist_ok=True)
        write_vehicle_spec_yaml(result.spec, args.write_spec)
        print(f"\nWrote {args.write_spec}")

    return 0 if result.gates_passed == 7 else 1


def _cmd_moodboard_blend_mesh(args: argparse.Namespace) -> int:
    from bucephalus.mesh_blend import write_blend_glb
    from bucephalus.mesh_paths import BLEND_OUTPUT
    from bucephalus.optimize import optimize_weights

    items = resolve_moodboard_coefficients()
    if args.use_optimized:
        base = load_vehicle_spec(DEFAULT_SPEC)
        opt = optimize_weights(items, base)
        pairs = [(c, opt.weights.get(c.slug, 0.0)) for c in items]
    else:
        total = sum(c.weight for c in items) or 1.0
        pairs = [(c, c.weight / total) for c in items]

    out = write_blend_glb(pairs, output=args.output or BLEND_OUTPUT, pitch_mm=args.pitch)
    print(f"Wrote blended mesh: {out}")
    return 0


def _cmd_moodboard_iterate(args: argparse.Namespace) -> int:
    base = load_vehicle_spec(args.base)
    items = resolve_moodboard_coefficients()
    start = blend_coefficients(items, slug="moodboard_centroid", model="centroid")

    if args.shortlist_first:
        candidates = pairwise_shortlist(items, args.shortlist)
        ranked = rank_shortlist(candidates, base)
        start = ranked[0][0]

    result = recursive_refine(
        start,
        items,
        base,
        max_passes=args.passes,
        step=args.step,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "converged": result.converged,
                    "passes": [
                        {
                            "pass": p.pass_index,
                            "penalty": round(p.penalty, 4),
                            "gates_passed": p.gates_passed,
                        }
                        for p in result.passes
                    ],
                    "final_coefficients": result.final_coeffs.numeric_vector(),
                    "final_gates": [
                        {"id": g.id, "passed": g.passed, "detail": g.detail}
                        for g in run_gates(result.final_spec).gates
                    ],
                },
                indent=2,
            )
        )
    else:
        print(f"# Recursive fit — {len(result.passes)} passes\n")
        for p in result.passes:
            print(f"pass {p.pass_index}: {p.gates_passed}/7 gates, penalty {p.penalty:.4f}")
        print()
        print(format_report(result.final_spec))

    if args.write_spec:
        args.write_spec.parent.mkdir(parents=True, exist_ok=True)
        from bucephalus.export_spec import write_vehicle_spec_yaml

        write_vehicle_spec_yaml(result.final_spec, args.write_spec)
        print(f"\nWrote {args.write_spec}")

    return 0 if result.converged else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bucephalus — transverse V10 H2 ICE packaging and feasibility gates",
    )
    sub = parser.add_subparsers(dest="command")

    p_eval = sub.add_parser("evaluate", help="Run gates on a vehicle YAML (default command)")
    p_eval.add_argument(
        "spec",
        type=Path,
        nargs="?",
        default=DEFAULT_SPEC,
        help="Vehicle YAML spec",
    )
    p_eval.add_argument("--json", action="store_true", help="JSON gate report")
    p_eval.set_defaults(func=_cmd_evaluate)

    mb = sub.add_parser("moodboard", help="Brand/model mood board → interpolate → iterate")
    mb_sub = mb.add_subparsers(dest="moodboard_command", required=True)

    p_list = mb_sub.add_parser("list", help="List mood-board entries")
    p_list.set_defaults(func=_cmd_moodboard_list)

    p_add = mb_sub.add_parser("add", help="Add brand/model to mood board")
    p_add.add_argument("--brand", help="Brand name (must match catalog)")
    p_add.add_argument("--model", help="Model name (must match catalog)")
    p_add.add_argument("--slug", help="Catalog slug instead of brand/model")
    p_add.add_argument("--weight", type=float, default=1.0, help="Preference weight")
    p_add.add_argument("--note", default="", help="Optional note")
    p_add.set_defaults(func=_cmd_moodboard_add)

    p_ext = mb_sub.add_parser("extract", help="Re-extract coefficients from meshes/ into catalog")
    p_ext.set_defaults(func=_cmd_moodboard_extract)

    p_short = mb_sub.add_parser("shortlist", help="Weighted blends + ranked shortlist")
    p_short.add_argument("--count", type=int, default=8, help="Max shortlist candidates")
    p_short.add_argument("--base", type=Path, default=DEFAULT_SPEC, help="Base concept YAML")
    p_short.add_argument("--json", action="store_true")
    p_short.set_defaults(func=_cmd_moodboard_shortlist)

    p_iter = mb_sub.add_parser("iterate", help="Recursive coefficient refinement toward gates")
    p_iter.add_argument("--passes", type=int, default=24, help="Max refinement passes")
    p_iter.add_argument("--step", type=float, default=0.35, help="Nudge step per pass (0–1)")
    p_iter.add_argument("--base", type=Path, default=DEFAULT_SPEC, help="Base concept YAML")
    p_iter.add_argument("--shortlist-first", action="store_true", help="Start from best shortlist blend")
    p_iter.add_argument("--shortlist", type=int, default=8, help="Shortlist size if --shortlist-first")
    p_iter.add_argument("--write-spec", type=Path, help="Write final interpolated YAML here")
    p_iter.add_argument("--json", action="store_true")
    p_iter.set_defaults(func=_cmd_moodboard_iterate)

    p_opt = mb_sub.add_parser("optimize", help="SLSQP weight optimization toward spec gates")
    p_opt.add_argument("--base", type=Path, default=DEFAULT_SPEC, help="Target concept YAML")
    p_opt.add_argument("--alpha", type=float, default=0.15, help="Target pull strength")
    p_opt.add_argument("--write-spec", type=Path, help="Write optimized YAML")
    p_opt.add_argument("--json", action="store_true")
    p_opt.set_defaults(func=_cmd_moodboard_optimize)

    p_mesh = mb_sub.add_parser("blend-mesh", help="SDF blend meshes using optimized or mood-board weights")
    p_mesh.add_argument("-o", "--output", type=Path, help="Output GLB path")
    p_mesh.add_argument("--pitch", type=float, default=25.0, help="Voxel pitch mm")
    p_mesh.add_argument("--use-optimized", action="store_true", help="Run optimizer first")
    p_mesh.set_defaults(func=_cmd_moodboard_blend_mesh)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Back-compat: `python -m bucephalus config/foo.yaml` without subcommand.
    if args.command is None:
        if argv and not str(argv[0]).startswith("-"):
            spec_path = Path(argv[0])
            if spec_path.suffix in (".yaml", ".yml"):
                return _cmd_evaluate(
                    argparse.Namespace(spec=spec_path, json="--json" in (argv or []))
                )
        return _cmd_evaluate(argparse.Namespace(spec=DEFAULT_SPEC, json=False))

    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
