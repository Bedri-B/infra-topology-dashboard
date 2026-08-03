# Infra Topology Dashboard

A small working demo of the core pattern behind infrastructure topology
tools: a **FastAPI + NetworkX** backend that turns a `hosts / vms /
services / edges` description into a fixed-seed force-directed layout, and
a **React + TypeScript** frontend that renders it as hand-rolled SVG --
no D3, no client-side layout math -- with node colors driven by a
simulated live-status feed the frontend polls every few seconds.

**All topology data is sample/generic** -- made-up hostnames
(`web-01`, `db-01`, ...), no real infrastructure, IPs, or hosting
provider details.

## System architecture

**Topology schema** (`backend/app/schemas.py`): a topology is `hosts`,
`vms`, `services`, and an `edges` list. VMs reference the host they run
on (`host_id`); services reference the VM they run in (`vm_id`); those
containment relationships become graph edges automatically. The `edges`
list is for everything else -- service-to-service dependencies, in this
demo's sample data, `api` and `worker` services depending on `postgres`
and `redis`. A Pydantic validator rejects topologies with dangling
references or duplicate node ids before any layout work happens.

**Layout** (`backend/app/layout.py`): builds a NetworkX graph from the
topology and runs `nx.spring_layout` with a fixed seed (`LAYOUT_SEED = 42`),
normalizing the result into a fixed canvas so the frontend renders
coordinates directly. Containment edges (host->vm, vm->service) are
weighted higher than dependency edges so a host's VMs cluster near it
instead of collapsing into their dependencies.

**Live status** (`backend/app/status_simulator.py`): there's no real
infrastructure behind this, so "live" status is simulated -- an in-memory
`StatusSimulator` holds a status per node and, on each tick, gives every
node a small independent chance to redraw its status from a weighted
transition matrix (`up` is sticky, `warn` is a plausible middle state,
`down` tends to recover). A background task ticks it every 4 seconds;
the frontend polls `GET /api/v1/topology/status` on the same cadence and
merges the result into the rendered graph, so node colors visibly drift
without a browser refresh.

**Rendering** (`frontend/src/TopologyView.tsx`): fetches the layout once,
then draws nodes as SVG shapes (rect for hosts, rotated-square/diamond for
VMs, circle for services) positioned exactly where the backend put them,
edges as SVG lines styled by kind (solid for containment, dashed for
dependencies), with a status/kind/edge legend. Pan is plain pointer-event
dragging and zoom is `viewBox` resizing on button clicks -- no d3-zoom, no
extra dependency.

## Why the layout is deterministic

Every layout call is seeded (`LAYOUT_SEED = 42`), so reloading the
dashboard, or diffing two runs in CI, produces identical node coordinates
every time for the same topology. `backend/tests/test_layout.py` asserts
this directly: same input + same seed -> identical `(x, y)` output.

## Backend

```
cd backend
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Endpoints:
- `GET /api/v1/topology/layout` -- layout for the bundled sample topology.
- `POST /api/v1/topology/layout` -- layout for an arbitrary `{hosts, vms, services, edges}` body (not persisted).
- `GET /api/v1/topology/status` -- current simulated status per node in the sample topology.
- `GET /api/v1/health` -- liveness check.

Run tests: `pytest` (31 tests, `backend/tests/`) -- layout determinism and
canvas bounds, containment-edge synthesis, the status simulator's
transition logic, and the API endpoints (including validation-error
cases).

## Frontend

```
cd frontend
npm install
cp .env.example .env   # point VITE_API_BASE at the backend if not localhost:8000
npm run dev
```

Run tests: `npm test` (17 tests, Vitest)

Pure, DOM-free logic lives outside components so it unit tests without a
browser: `src/statusColor.ts` (status -> color/label mapping, worst-status
rollup) and `src/topologyTransform.ts` (merging a live status snapshot
into layout nodes, grouping/counting by kind and status).

## Deliberate simplifications (this is a portfolio demo, not a product)

- Status is simulated in-memory, not read from any real health-check,
  agent, or monitoring system -- there's nothing to connect to.
- The status simulator's state resets on backend restart; nothing is
  persisted (no database in this demo).
- The bundled sample topology is small on purpose (3 hosts, 3 VMs, 5
  services, 14 edges) -- enough to show containment + dependency edges
  and every node kind, not a stress test of the layout algorithm.
- Pan/zoom is intentionally minimal (drag to pan, button zoom via
  `viewBox`) rather than a full gesture/wheel-zoom implementation.
