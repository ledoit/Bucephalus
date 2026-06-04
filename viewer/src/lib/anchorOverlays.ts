import { Box3, Group, Object3D, Vector3 } from "three";
import type { BucephalusScene } from "./sceneTypes";

/** Read engine-bay anchor from exported scene (mm, vehicle-centered). */
export function engineAnchorFromScene(data: BucephalusScene): Vector3 {
  const bay = data.primitives.find((p) => p.id === "bay_envelope");
  if (bay && bay.kind === "box") {
    return new Vector3(...bay.center_mm);
  }
  return new Vector3(-0.12 * data.wheelbase_mm, 0, 400);
}

/**
 * Shift packaging overlays so engine bay sits in the rear-mid floor pan of the shell.
 */
export function anchorOverlaysToShell(
  overlayRoot: Group,
  shellRoot: Object3D,
  specAnchor: Vector3,
): void {
  const box = new Box3().setFromObject(shellRoot);
  if (box.isEmpty()) return;

  const size = new Vector3();
  const min = box.min;
  box.getSize(size);

  const target = new Vector3(
    min.x + 0.44 * size.x,
    min.y + 0.5 * size.y,
    min.z + 0.2 * size.z,
  );
  overlayRoot.position.copy(target.sub(specAnchor));
}
