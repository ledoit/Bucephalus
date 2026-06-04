import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Vector3 } from "three";
import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import type { VehicleShell } from "./sceneTypes";

const DRACO_DECODER =
  "https://www.gstatic.com/draco/versioned/decoders/1.5.6/";

let loader: GLTFLoader | null = null;

function getLoader(): GLTFLoader {
  if (!loader) {
    const draco = new DRACOLoader();
    draco.setDecoderPath(DRACO_DECODER);
    const gltf = new GLTFLoader();
    gltf.setDRACOLoader(draco);
    loader = gltf;
  }
  return loader;
}

/** Fit loaded mesh: mm coords, Z-up, origin = vehicle center on ground. */
export function fitShellToLayout(
  root: Object3D,
  shell: VehicleShell,
): void {
  const rot = shell.rotation_deg ?? [-90, 90, 0];
  root.rotation.set(
    (rot[0] * Math.PI) / 180,
    (rot[1] * Math.PI) / 180,
    (rot[2] * Math.PI) / 180,
  );

  const box = new Box3().setFromObject(root);
  const size = new Vector3();
  const center = new Vector3();
  box.getSize(size);
  box.getCenter(center);

  // Fore-aft span along X after rotation (Ferrari GLB default orientation).
  const lengthAlongX = size.x;
  const scale = shell.target_length_mm / Math.max(lengthAlongX, 1);
  root.scale.setScalar(scale);

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

function applyShellMaterials(root: Object3D, opacity: number) {
  root.traverse((obj) => {
    if (!(obj instanceof Mesh)) return;
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    obj.material = mats.map((m) => {
      const base = new MeshStandardMaterial({
        color: "#c8ccd4",
        metalness: 0.55,
        roughness: 0.35,
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
  const gltf = await getLoader().loadAsync(shell.url);
  const root = new Group();
  root.name = "vehicle-shell";
  root.userData = { label: shell.name, group: "shell" };
  root.add(gltf.scene);

  applyShellMaterials(root, shell.opacity ?? 0.88);
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
