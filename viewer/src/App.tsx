import { useCallback, useEffect, useRef, useState } from "react";
import { buildSceneMeshes } from "./lib/buildSceneMeshes";
import { loadVehicleShell } from "./lib/loadVehicleShell";
import type { BucephalusScene, VehicleShell } from "./lib/sceneTypes";
import { createThreeHost, type ThreeHost } from "./lib/threeHost";
import "./App.css";

type LoadState =
  | { kind: "loading"; message: string }
  | { kind: "ready"; scene: BucephalusScene }
  | { kind: "error"; message: string };

const LEGEND: { group: string; label: string }[] = [
  { group: "shell", label: "Reference car shell (glTF)" },
  { group: "bay", label: "Bay IML" },
  { group: "powertrain", label: "V10 envelope + banks" },
  { group: "storage_void", label: "H₂ packaging voids" },
  { group: "tanks", label: "700 bar tanks (tentative)" },
];

function App() {
  const viewportRef = useRef<HTMLDivElement>(null);
  const hostRef = useRef<ThreeHost | null>(null);
  const meshesRef = useRef<{ root: import("three").Object3D; dispose: () => void } | null>(
    null,
  );
  const shellRef = useRef<{ dispose: () => void } | null>(null);
  const shellUrlRef = useRef<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const shellInputRef = useRef<HTMLInputElement>(null);
  const sceneRef = useRef<BucephalusScene | null>(null);

  const [load, setLoad] = useState<LoadState>({
    kind: "loading",
    message: "Loading scene…",
  });
  const [showGrid, setShowGrid] = useState(true);
  const [hiddenGroups, setHiddenGroups] = useState<Set<string>>(new Set());

  const clearContent = useCallback((host: ThreeHost) => {
    meshesRef.current?.dispose();
    meshesRef.current = null;
    shellRef.current?.dispose();
    shellRef.current = null;
    if (shellUrlRef.current) {
      URL.revokeObjectURL(shellUrlRef.current);
      shellUrlRef.current = null;
    }
    for (const child of [...host.contentRoot.children]) {
      host.contentRoot.remove(child);
    }
  }, []);

  const applyScene = useCallback(
    async (data: BucephalusScene) => {
      const host = hostRef.current;
      if (!host) return;
      clearContent(host);

      if (data.vehicle_shell) {
        setLoad({ kind: "loading", message: "Loading reference shell…" });
        const { root, dispose } = await loadVehicleShell(data.vehicle_shell);
        shellRef.current = { dispose };
        host.contentRoot.add(root);
      }

      meshesRef.current = buildSceneMeshes(host, data, { fitCamera: false });
      host.fitCamera();
      sceneRef.current = data;
      setLoad({ kind: "ready", scene: data });
    },
    [clearContent],
  );

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const host = createThreeHost(el);
    hostRef.current = host;
    return () => {
      clearContent(host);
      host.dispose();
      hostRef.current = null;
    };
  }, [clearContent]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.grid.visible = showGrid;
  }, [showGrid]);

  useEffect(() => {
    void (async () => {
      try {
        const res = await fetch("/scene.json");
        if (!res.ok) throw new Error(`scene.json ${res.status}`);
        const data = (await res.json()) as BucephalusScene;
        await applyScene(data);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setLoad({
          kind: "error",
          message: `${msg} — export with: python -m bucephalus config/bucephalus_v0.yaml --export-scene viewer/public/scene.json`,
        });
      }
    })();
  }, [applyScene]);

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    host.contentRoot.traverse((obj) => {
      const group = obj.userData.group as string | undefined;
      if (!group) return;
      obj.visible = !hiddenGroups.has(group);
    });
  }, [hiddenGroups, load]);

  const onSceneFile = async (files: FileList | null) => {
    const file = files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      await applyScene(JSON.parse(text) as BucephalusScene);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setLoad({ kind: "error", message: msg });
    }
  };

  const onShellFile = async (files: FileList | null) => {
    const file = files?.[0];
    const base = sceneRef.current;
    if (!file || !base?.vehicle_shell) return;
    const url = URL.createObjectURL(file);
    if (shellUrlRef.current) URL.revokeObjectURL(shellUrlRef.current);
    shellUrlRef.current = url;
    const shell: VehicleShell = {
      ...base.vehicle_shell,
      url,
      name: file.name,
      license: "User upload",
    };
    await applyScene({ ...base, vehicle_shell: shell });
  };

  const toggleGroup = (group: string) => {
    setHiddenGroups((prev) => {
      const next = new Set(prev);
      if (next.has(group)) next.delete(group);
      else next.add(group);
      return next;
    });
  };

  const scene = load.kind === "ready" ? load.scene : null;
  const statusText =
    load.kind === "loading"
      ? load.message
      : load.kind === "error"
        ? load.message
        : `${scene!.vehicle} · ${scene!.summary.gates_passed ? "GO" : "NO-GO"} · Orbit: drag · Zoom: scroll`;

  return (
    <div className="app">
      <header className="toolbar">
        <div className="brand">
          <span className="brand-name">Bucephalus</span>
          <span className="brand-tag">Reference shell + packaging overlays</span>
        </div>
        <div className="toolbar-actions">
          <button type="button" onClick={() => fileInputRef.current?.click()}>
            Scene JSON…
          </button>
          <button type="button" onClick={() => shellInputRef.current?.click()}>
            Replace shell (glb)…
          </button>
          <button type="button" onClick={() => hostRef.current?.fitCamera()}>
            Frame scene
          </button>
          <label className="toggle">
            <input
              type="checkbox"
              checked={showGrid}
              onChange={(e) => setShowGrid(e.target.checked)}
            />
            Grid
          </label>
        </div>
      </header>

      <input
        ref={fileInputRef}
        type="file"
        className="file-input"
        accept=".json,application/json"
        onChange={(e) => {
          void onSceneFile(e.target.files);
          e.target.value = "";
        }}
      />
      <input
        ref={shellInputRef}
        type="file"
        className="file-input"
        accept=".glb,.gltf,model/gltf-binary"
        onChange={(e) => {
          void onShellFile(e.target.files);
          e.target.value = "";
        }}
      />

      <main className="viewport" ref={viewportRef}>
        {load.kind === "error" && (
          <div className="drop-hint">
            <p>No scene loaded</p>
            <p className="muted small">{load.message}</p>
          </div>
        )}
      </main>

      <footer className={`status status-${load.kind}`}>{statusText}</footer>

      <aside className="panel">
        <h2>Legend</h2>
        <ul className="legend">
          {LEGEND.map(({ group, label }) => (
            <li key={group}>
              <label>
                <input
                  type="checkbox"
                  checked={!hiddenGroups.has(group)}
                  onChange={() => toggleGroup(group)}
                />
                {label}
              </label>
            </li>
          ))}
        </ul>

        {scene?.vehicle_shell && (
          <>
            <h2>Vehicle shell</h2>
            <p className="muted small">{scene.vehicle_shell.name}</p>
            {scene.vehicle_shell.replace_hint && (
              <p className="muted small">{scene.vehicle_shell.replace_hint}</p>
            )}
          </>
        )}

        {scene && (
          <>
            <h2>Summary</h2>
            <dl className="facts">
              <dt>Engine</dt>
              <dd>{scene.summary.engine_source}</dd>
              <dt>Transverse fit</dt>
              <dd>{scene.summary.transverse_fits ? "yes" : "no"}</dd>
              <dt>H₂ onboard</dt>
              <dd>{scene.summary.h2_kg} kg</dd>
              <dt>Curb budget</dt>
              <dd>
                {scene.summary.curb_kg} kg (
                {scene.summary.curb_delta_kg >= 0 ? "+" : ""}
                {scene.summary.curb_delta_kg} kg)
              </dd>
            </dl>

            <h2>Gates</h2>
            <ul className="gates">
              {scene.gates.map((g) => (
                <li key={g.id} className={g.passed ? "pass" : "fail"}>
                  <code>{g.id}</code>
                  <span className="muted">{g.detail}</span>
                </li>
              ))}
            </ul>
          </>
        )}

        <p className="muted note">{scene?.note}</p>
      </aside>
    </div>
  );
}

export default App;
