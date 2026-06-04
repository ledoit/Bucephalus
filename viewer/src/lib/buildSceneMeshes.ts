import {
  BoxGeometry,
  Color,
  CylinderGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  Object3D,
  Quaternion,
  SphereGeometry,
  Vector3,
} from "three";
import type { Axis, BucephalusScene, ScenePrimitive } from "./sceneTypes";
import { normalizePrimitive } from "./sceneTypes";
import type { ThreeHost } from "./threeHost";

const GROUP_COLORS: Record<string, number> = {
  body: 0x4a5568,
  bay: 0x5b8def,
  powertrain: 0xe8a838,
  storage_void: 0x3ecf8e,
  tanks: 0x2dd4bf,
};

const AXIS_ROT: Record<Axis, Quaternion> = {
  x: new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), new Vector3(1, 0, 0)),
  y: new Quaternion(),
  z: new Quaternion().setFromUnitVectors(new Vector3(0, 1, 0), new Vector3(0, 0, 1)),
};

function addMesh(
  root: Group,
  geo: BoxGeometry | CylinderGeometry | SphereGeometry,
  mat: MeshBasicMaterial,
  position: [number, number, number],
  rotation: Quaternion | undefined,
  id: string,
  label: string,
  group: string | undefined,
  disposables: (() => void)[],
) {
  const mesh = new Mesh(geo, mat);
  mesh.position.set(...position);
  if (rotation) mesh.quaternion.copy(rotation);
  mesh.name = id;
  mesh.userData = { label, group };
  root.add(mesh);
  disposables.push(() => {
    geo.dispose();
    mat.dispose();
  });
}

function materialFor(
  color: string | undefined,
  group: string,
  opacity: number,
  wireframe: boolean,
) {
  const c = new Color(color || GROUP_COLORS[group] || 0x888888);
  return new MeshBasicMaterial({
    color: c,
    transparent: opacity < 1,
    opacity,
    wireframe,
    depthWrite: !wireframe && opacity > 0.5,
  });
}

function addPrimitive(
  root: Group,
  p: ScenePrimitive,
  disposables: (() => void)[],
) {
  const mat = materialFor(p.color, p.group, p.opacity, p.wireframe ?? false);
  const [cx, cy, cz] = p.center_mm;

  if (p.kind === "cylinder") {
    const geo = new CylinderGeometry(p.radius_mm, p.radius_mm, p.length_mm, 24);
    addMesh(
      root,
      geo,
      mat,
      [cx, cy, cz],
      AXIS_ROT[p.axis],
      p.id,
      p.label,
      p.group,
      disposables,
    );
    return;
  }

  const [sx, sy, sz] = p.size_mm;
  const geo = new BoxGeometry(sx, sy, sz);
  addMesh(root, geo, mat, [cx, cy, cz], undefined, p.id, p.label, p.group, disposables);
}

export function buildSceneMeshes(
  host: ThreeHost,
  data: BucephalusScene,
): { root: Object3D; dispose: () => void } {
  const root = new Group();
  root.name = "bucephalus-scene";
  const disposables: (() => void)[] = [];

  for (const raw of data.primitives) {
    addPrimitive(root, normalizePrimitive(raw), disposables);
  }

  for (const m of data.markers) {
    const geo = new SphereGeometry(m.radius_mm, 20, 16);
    const mat = new MeshBasicMaterial({
      color: new Color(m.color),
      transparent: true,
      opacity: 0.9,
    });
    addMesh(
      root,
      geo,
      mat,
      m.position_mm,
      undefined,
      m.id,
      m.label,
      undefined,
      disposables,
    );
  }

  host.contentRoot.add(root);
  host.fitCamera();

  return {
    root,
    dispose() {
      host.contentRoot.remove(root);
      disposables.forEach((d) => d());
    },
  };
}
