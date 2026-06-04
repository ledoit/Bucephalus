import { useCallback, useEffect, useRef, useState } from "react";
import { buildSceneMeshes } from "./lib/buildSceneMeshes";
import type { BucephalusScene } from "./lib/sceneTypes";
import { createThreeHost, type ThreeHost } from "./lib/threeHost";
import "./App.css";

type LoadState =
  | { kind: "loading" }
  | { kind: "ready"; scene: BucephalusScene }
  | { kind: "error"; message: string };

const LEGEND: { group: string; label: string }[] = [
  { group: "body", label: "Body shell" },
  { group: "bay", label: "Bay IML" },
  { group: "powertrain", label: "Engine / clearance" },
  { group: "storage_void", label: "H₂ packaging voids" },
  { group: "tanks", label: "700 bar tanks (tentative)" },
];

function App() {
  const viewportRef = useRef<HTMLDivElement>(null);
  const hostRef = useRef<ThreeHost | null>(null);
  const meshesRef = useRef<{ root: import("three").Object3D; dispose: () => void } | null>(
    null,
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [load, setLoad] = useState<LoadState>({ kind: "loading" });
  const [showGrid, setShowGrid] = useState(true);
  const [hiddenGroups, setHiddenGroups] = useState<Set<string>>(new Set());

  const applyScene = useCallback((data: BucephalusScene) => {
    const host = hostRef.current;
    if (!host) return;
    meshesRef.current?.dispose();
    meshesRef.current = buildSceneMeshes(host, data);
    setLoad({ kind: "ready", scene: data });
  }, []);

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const host = createThreeHost(el);
    hostRef.current = host;
    return () => {
      meshesRef.current?.dispose();
      host.dispose();
      hostRef.current = null;
    };
  }, []);

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
        applyScene(data);
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
    const root = meshesRef.current?.root;
    if (!host || !root) return;
    root.traverse((obj) => {
      const group = obj.userData.group as string | undefined;
      if (!group) return;
      obj.visible = !hiddenGroups.has(group);
    });
  }, [hiddenGroups, load]);

  const onFile = async (files: FileList | null) => {
    const file = files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      applyScene(JSON.parse(text) as BucephalusScene);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setLoad({ kind: "error", message: msg });
    }
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
      ? "Loading scene.json…"
      : load.kind === "error"
        ? load.message
        : `${scene!.vehicle} · ${scene!.summary.gates_passed ? "GO" : "NO-GO"} · Orbit: drag · Zoom: scroll`;

  return (
    <div className="app">
      <header className="toolbar">
        <div className="brand">
          <span className="brand-name">Bucephalus</span>
          <span className="brand-tag">Tentative packaging blocks</span>
        </div>
        <div className="toolbar-actions">
          <button type="button" onClick={() => fileInputRef.current?.click()}>
            Open scene JSON…
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
          void onFile(e.target.files);
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

        <p className="muted note">
          {scene?.note ??
            "Block positions are placeholders until bay IML and tank CAD are measured."}
        </p>
      </aside>
    </div>
  );
}

export default App;
