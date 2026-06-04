import {
  BoxGeometry,
  Color,
  Group,
  Mesh,
  MeshBasicMaterial,
  Object3D,
  SphereGeometry,
} from "three";
import type { BucephalusScene } from "./sceneTypes";
import type { ThreeHost } from "./threeHost";

const GROUP_COLORS: Record<string, number> = {
  body: 0x4a5568,
  bay: 0x5b8def,
  powertrain: 0xe8a838,
  storage_void: 0x3ecf8e,
  tanks: 0x2dd4bf,
};

export function buildSceneMeshes(
  host: ThreeHost,
  data: BucephalusScene,
): { root: Object3D; dispose: () => void } {
  const root = new Group();
  root.name = "bucephalus-scene";
  const disposables: (() => void)[] = [];

  for (const p of data.primitives) {
    const [sx, sy, sz] = p.size_mm;
    const geo = new BoxGeometry(sx, sy, sz);
    const color = new Color(p.color || GROUP_COLORS[p.group] || 0x888888);
    const mat = new MeshBasicMaterial({
      color,
      transparent: p.opacity < 1,
      opacity: p.opacity,
      wireframe: p.wireframe ?? false,
      depthWrite: !(p.wireframe ?? false) && p.opacity > 0.5,
    });
    const mesh = new Mesh(geo, mat);
    const [cx, cy, cz] = p.center_mm;
    mesh.position.set(cx, cy, cz);
    mesh.name = p.id;
    mesh.userData = { label: p.label, group: p.group };
    root.add(mesh);
    disposables.push(() => {
      geo.dispose();
      mat.dispose();
    });
  }

  for (const m of data.markers) {
    const r = m.radius_mm;
    const geo = new SphereGeometry(r, 20, 16);
    const mat = new MeshBasicMaterial({
      color: new Color(m.color),
      transparent: true,
      opacity: 0.9,
    });
    const mesh = new Mesh(geo, mat);
    const [px, py, pz] = m.position_mm;
    mesh.position.set(px, py, pz);
    mesh.name = m.id;
    mesh.userData = { label: m.label };
    root.add(mesh);
    disposables.push(() => {
      geo.dispose();
      mat.dispose();
    });
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
