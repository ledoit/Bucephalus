export type BoxPrimitive = {
  id: string;
  label: string;
  group: string;
  center_mm: [number, number, number];
  size_mm: [number, number, number];
  color: string;
  opacity: number;
  wireframe?: boolean;
};

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
  wheelbase_mm: number;
  track_front_mm: number;
  track_rear_mm: number;
  primitives: BoxPrimitive[];
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
