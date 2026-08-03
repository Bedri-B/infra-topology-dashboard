import { useEffect, useRef, useState } from "react";
import { fetchSampleLayout, fetchStatus } from "./api";
import TopologyView from "./TopologyView";
import { countByStatus, mergeNodeStatuses } from "./topologyTransform";
import { statusToLabel } from "./statusColor";
import type { LayoutResponse } from "./types";

const STATUS_POLL_MS = 4000;

type LoadState = "loading" | "ready" | "error";

export default function App() {
  const [layout, setLayout] = useState<LayoutResponse | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [lastTick, setLastTick] = useState<number | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;

    fetchSampleLayout()
      .then((data) => {
        if (cancelled) return;
        setLayout(data);
        setLoadState("ready");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : String(err));
        setLoadState("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (loadState !== "ready") return;

    let cancelled = false;

    async function poll() {
      try {
        const status = await fetchStatus();
        if (cancelled) return;
        setLastTick(status.tick);
        setLayout((current) => {
          if (!current) return current;
          return { ...current, nodes: mergeNodeStatuses(current.nodes, status.statuses) };
        });
      } catch {
        // A missed poll isn't fatal -- the dashboard just keeps showing the
        // last known statuses until the next tick succeeds.
      }
    }

    poll();
    pollRef.current = window.setInterval(poll, STATUS_POLL_MS);
    return () => {
      cancelled = true;
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    };
  }, [loadState]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <p className="eyebrow">Infra Topology Dashboard</p>
        <h1>Sample infrastructure topology</h1>
        <p className="subtitle">
          Hosts, VMs and services laid out server-side with a fixed-seed NetworkX spring
          layout, statuses refreshed by polling a simulated live-status endpoint. All data
          below is a bundled sample topology (made-up hostnames) &mdash; not a connection to
          any real infrastructure.
        </p>
      </header>

      <main>
        {loadState === "loading" && <p className="status-line">Fetching layout from the API&hellip;</p>}
        {loadState === "error" && (
          <p className="status-line status-error">
            Couldn&apos;t reach the backend: {error}. Is <code>uvicorn app.main:app</code> running on{" "}
            <code>VITE_API_BASE</code>?
          </p>
        )}
        {loadState === "ready" && layout && (
          <>
            <StatusSummary layout={layout} tick={lastTick} />
            <TopologyView data={layout} />
          </>
        )}
      </main>

      <footer className="app-footer">
        Sample/generic topology data for demo purposes only &mdash; no real hosts, IPs, or
        infrastructure details. Layout: NetworkX <code>spring_layout</code> (seed{" "}
        {layout?.seed ?? "-"}). Status: in-memory simulator, polled every{" "}
        {STATUS_POLL_MS / 1000}s.
      </footer>
    </div>
  );
}

function StatusSummary({ layout, tick }: { layout: LayoutResponse; tick: number | null }) {
  const counts = countByStatus(layout.nodes);
  return (
    <div className="status-summary">
      {(["up", "warn", "down"] as const).map((status) => (
        <span key={status} className={`status-pill status-pill-${status}`}>
          {counts[status]} {statusToLabel(status)}
        </span>
      ))}
      <span className="status-summary-tick">tick {tick ?? 0}</span>
    </div>
  );
}
