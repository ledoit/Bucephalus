import { Box3, Group, Object3D, Vector3 } from "three";
import type { BucephalusScene } from "./sceneTypes";

export type ShellBounds = {
  min: Vector3;
  size: Vector3;
};

export function shellBounds(shellRoot: Object3D): ShellBounds | null {
  const box = new Box3().setFromObject(shellRoot);
  if (box.isEmpty()) return null;
  const size = new Vector3();
  box.getSize(size);
  return { min: box.min.clone(), size };
}

/** Place bay, engine, and tanks on plausible regions of the loaded shell (mid-engine coupe). */
export function layoutPackagingOnShell(
  overlayRoot: Group,
  shellRoot: Object3D,
  data: BucephalusScene,
): void {
  const b = shellBounds(shellRoot);
  if (!b) return;

  overlayRoot.position.set(0, 0, 0);
  const { min, size } = b;
  const halfWb = data.wheelbase_mm / 2;
  const track = Math.max(data.track_front_mm, data.track_rear_mm);

  const engineCenter = new Vector3(
    min.x + 0.46 * size.x,
    min.y + 0.5 * size.y,
    min.z + 0.22 * size.z,
  );

  overlayRoot.traverse((obj) => {
    const id = obj.name;
    if (!id) return;

    if (id === "bay_envelope") {
      const bay = data.primitives.find((p) => p.id === "bay_envelope");
      const h = bay?.kind === "box" ? bay.size_mm[2] : 400;
      obj.position.copy(engineCenter);
      obj.position.z += h * 0.45;
      return;
    }

    if (id === "engine_block") {
      obj.position.copy(engineCenter);
      return;
    }

    if (id.startsWith("tank_")) {
      const label = (obj.userData.label as string) || "";
      if (label.includes("tunnel")) {
        obj.position.set(
          min.x + 0.36 * size.x,
          min.y + 0.5 * size.y,
          min.z + 0.11 * size.z,
        );
      } else if (label.includes("underfloor")) {
        obj.position.set(
          min.x + 0.58 * size.x,
          min.y + 0.5 * size.y,
          min.z + 0.07 * size.z,
        );
      }
    }
  });

  layoutAxlesAndCg(overlayRoot, data, min, size, halfWb, track);
}

function layoutAxlesAndCg(
  overlayRoot: Group,
  data: BucephalusScene,
  min: Vector3,
  size: Vector3,
  halfWb: number,
  track: number,
) {
  const wheelZ = min.z + size.z * 0.13;
  overlayRoot.traverse((obj) => {
    if (obj.name === "rear_axle") {
      obj.position.set(-halfWb, min.y + 0.5 * size.y, wheelZ);
    }
    if (obj.name === "front_axle") {
      obj.position.set(halfWb, min.y + 0.5 * size.y, wheelZ);
    }
    if (obj.name === "cg_total") {
      obj.position.set(
        min.x + 0.52 * size.x,
        min.y + 0.5 * size.y,
        min.z + 0.38 * size.z,
      );
    }
  });
}
