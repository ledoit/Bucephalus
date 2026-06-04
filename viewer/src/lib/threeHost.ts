import {
  AmbientLight,
  Box3,
  Clock,
  DirectionalLight,
  GridHelper,
  HemisphereLight,
  ACESFilmicToneMapping,
  Object3D,
  PerspectiveCamera,
  Scene,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

export type ThreeHost = {
  scene: Scene;
  camera: PerspectiveCamera;
  renderer: WebGLRenderer;
  controls: OrbitControls;
  clock: Clock;
  grid: GridHelper;
  contentRoot: Object3D;
  fitCamera: () => void;
  setOnRender: (fn: (dt: number) => void) => void;
  dispose: () => void;
};

export function createThreeHost(container: HTMLElement): ThreeHost {
  const scene = new Scene();
  const camera = new PerspectiveCamera(
    50,
    container.clientWidth / Math.max(container.clientHeight, 1),
    1,
    500_000,
  );
  camera.position.set(3500, 2800, 5200);

  const renderer = new WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.setClearColor(0x0c0e12, 1);
  container.appendChild(renderer.domElement);

  scene.add(new HemisphereLight(0xe8ecf4, 0x1a2030, 0.55));
  scene.add(new AmbientLight(0xffffff, 0.25));
  const key = new DirectionalLight(0xffffff, 1.1);
  key.position.set(4000, 6000, 5000);
  scene.add(key);
  const fill = new DirectionalLight(0x8eb4ff, 0.35);
  fill.position.set(-5000, 2000, -3000);
  scene.add(fill);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  const grid = new GridHelper(8000, 40, 0x3a4254, 0x252a36);
  grid.position.y = 0;
  scene.add(grid);

  const contentRoot = new Object3D();
  contentRoot.name = "content";
  scene.add(contentRoot);

  const clock = new Clock();
  let onRender: (dt: number) => void = () => {};
  let raf = 0;

  const resize = () => {
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w < 1 || h < 1) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h, false);
  };

  const ro = new ResizeObserver(resize);
  ro.observe(container);
  resize();

  const renderLoop = () => {
    raf = requestAnimationFrame(renderLoop);
    const dt = clock.getDelta();
    controls.update();
    onRender(dt);
    renderer.render(scene, camera);
  };
  raf = requestAnimationFrame(renderLoop);

  const fitCamera = () => {
    const hide = [grid];
    const parents = hide.map((o) => o.parent);
    hide.forEach((o) => scene.remove(o));
    fitCameraToObject(camera, controls, contentRoot, 1.4);
    hide.forEach((o, i) => parents[i]?.add(o));
  };

  return {
    scene,
    camera,
    renderer,
    controls,
    clock,
    grid,
    contentRoot,
    fitCamera,
    setOnRender(fn) {
      onRender = fn;
    },
    dispose() {
      cancelAnimationFrame(raf);
      ro.disconnect();
      controls.dispose();
      renderer.dispose();
      container.removeChild(renderer.domElement);
    },
  };
}

function fitCameraToObject(
  camera: PerspectiveCamera,
  controls: OrbitControls,
  root: Object3D,
  fitOffset = 1.35,
) {
  const box = new Box3().setFromObject(root);
  if (box.isEmpty()) return;

  const size = new Vector3();
  const center = new Vector3();
  box.getSize(size);
  box.getCenter(center);

  const maxSize = Math.max(size.x, size.y, size.z);
  const fitHeightDistance =
    maxSize / (2 * Math.atan((Math.PI * camera.fov) / 360));
  const fitWidthDistance = fitHeightDistance / camera.aspect;
  const distance = fitOffset * Math.max(fitHeightDistance, fitWidthDistance);

  const direction = controls.target
    .clone()
    .sub(camera.position)
    .normalize()
    .multiplyScalar(distance);

  controls.maxDistance = distance * 20;
  controls.target.copy(center);
  camera.near = Math.max(distance / 200, 1);
  camera.far = distance * 200;
  camera.updateProjectionMatrix();
  camera.position.copy(controls.target).sub(direction);
  controls.update();
}
