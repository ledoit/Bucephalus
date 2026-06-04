import {
  Box3,
  Group,
  Mesh,
  MeshStandardMaterial,
  Object3D,
  Quaternion,
  Vector3,
} from "three";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { assetUrl } from "./assetUrl";
import type { VehicleShell } from "./sceneTypes";

let loader: GLTFLoader | null = null;

function getLoader(): GLTFLoader {
  if (!loader) {
    const draco = new DRACOLoader();
    draco.setDecoderPath(assetUrl("draco/"));
    const gltf = new GLTFLoader();
    gltf.setDRACOLoader(draco);
    loader = gltf;
  }
  return loader;
}

export function fitShellToLayout(root: Object3D, shell: VehicleShell): void {
  root.rotation.set(0, 0, 0);
  root.quaternion.identity();
  alignLongestAxisToX(root);

  if (shell.rotation_deg?.length === 3) {
    const [rx, ry, rz] = shell.rotation_deg;
    root.rotateX((rx * Math.PI) / 180);
    root.rotateY((ry * Math.PI) / 180);
    root.rotateZ((rz * Math.PI) / 180);
  }

  const box = new Box3().setFromObject(root);
  const size = new Vector3();
  box.getSize(size);
  const scale = shell.target_length_mm / Math.max(size.x, 1e-6);
  root.scale.setScalar(scale);

  const center = new Vector3();
  box.setFromObject(root);
  box.getCenter(center);
  root.position.sub(center);
  box.setFromObject(root);
  root.position.z -= box.min.z;

  const off = shell.offset_mm ?? [0, 0, 0];
  root.position.x += off[0];
  root.position.y += off[1];
  root.position.z += off[2];
}

function alignLongestAxisToX(root: Object3D): void {
  let bestLen = 0;
  let bestQ = new Quaternion();

  const candidates = [
    new Quaternion(),
    new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), Math.PI / 2),
    new Quaternion().setFromAxisAngle(new Vector3(0, 0, 1), -Math.PI / 2),
    new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), Math.PI / 2),
    new Quaternion().setFromAxisAngle(new Vector3(1, 0, 0), -Math.PI / 2),
    new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), Math.PI / 2),
    new Quaternion().setFromAxisAngle(new Vector3(0, 1, 0), -Math.PI / 2),
  ];

  for (const cand of candidates) {
    root.quaternion.copy(cand);
    const b = new Box3().setFromObject(root);
    const s = new Vector3();
    b.getSize(s);
    if (s.x > bestLen) {
      bestLen = s.x;
      bestQ.copy(cand);
    }
  }
  root.quaternion.copy(bestQ);
}

function applyShellMaterials(root: Object3D, opacity: number) {
  root.traverse((obj) => {
    if (!(obj instanceof Mesh)) return;
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    obj.material = mats.map((m) => {
      const base = new MeshStandardMaterial({
        color: "#b8bcc6",
        metalness: 0.65,
        roughness: 0.28,
        transparent: opacity < 1,
        opacity,
      });
      if ("map" in m && m.map) base.map = m.map;
      return base;
    });
  });
}

export async function loadVehicleShell(
  shell: VehicleShell,
): Promise<{ root: Group; dispose: () => void }> {
  const url = assetUrl(shell.url.replace(/^\//, ""));
  const gltf = await getLoader().loadAsync(url);
  const root = new Group();
  root.name = "vehicle-shell";
  root.userData = { label: shell.name, group: "shell" };
  root.add(gltf.scene);

  applyShellMaterials(root, shell.opacity ?? 1);
  fitShellToLayout(root, shell);

  const dispose = () => {
    root.traverse((obj) => {
      if (obj instanceof Mesh) {
        const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        mats.forEach((m) => m.dispose());
        obj.geometry?.dispose();
      }
    });
  };

  return { root, dispose };
}
