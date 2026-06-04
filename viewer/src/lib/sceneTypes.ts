export type Axis = "x" | "y" | "z";

export type BoxPrimitive = {
  kind: "box";
  id: string;
  label: string;
  group: string;
  center_mm: [number, number, number];
  size_mm: [number, number, number];
  color: string;
  opacity: number;
  wireframe?: boolean;
};

export type CylinderPrimitive = {
  kind: "cylinder";
  id: string;
  label: string;
  group: string;
  center_mm: [number, number, number];
  radius_mm: number;
  length_mm: number;
  axis: Axis;
  color: string;
  opacity: number;
  wireframe?: boolean;
};

export type ScenePrimitive = BoxPrimitive | CylinderPrimitive;

export type Marker = {
  id: string;
  label: string;
  position_mm: [number, number, number];
  color: string;
  radius_mm: number;
};

export type GateRow = {
  id: string;
  passed: boolean;
  detail: string;
};

export type BucephalusScene = {
  version: number;
  vehicle: string;
  units: string;
  axes: Record<string, string>;
  note: string;
  layout_source?: string;
  wheelbase_mm: number;
  track_front_mm: number;
  track_rear_mm: number;
  primitives: ScenePrimitive[];
  markers: Marker[];
  summary: {
    engine_source: string;
    transverse_fits: boolean;
    h2_kg: number;
    curb_kg: number;
    curb_delta_kg: number;
    gates_passed: boolean;
  };
  gates: GateRow[];
};

/** v1 scenes used boxes only (no kind field). */
export function normalizePrimitive(
  raw: ScenePrimitive & { kind?: string; size_mm?: [number, number, number] },
): ScenePrimitive {
  if (raw.kind === "cylinder") return raw as CylinderPrimitive;
  if (raw.kind === "box") return raw as BoxPrimitive;
  if (raw.size_mm) return { ...raw, kind: "box" } as BoxPrimitive;
  return raw as ScenePrimitive;
}
