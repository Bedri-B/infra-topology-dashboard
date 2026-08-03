"""FastAPI app: topology layout + simulated live status.

Two endpoints do the real work:

- `GET/POST /api/v1/topology/layout` -- compute a deterministic NetworkX
  layout for a topology. GET returns the bundled sample topology's layout;
  POST accepts an arbitrary `{hosts, vms, services, edges}` body and returns
  the layout for that instead (not persisted).
- `GET /api/v1/topology/status` -- current simulated status for every node
  in the bundled sample topology. A background task ticks the simulator
  every few seconds so polling clients see statuses drift over time without
  any real infrastructure behind them.
"""

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .layout import build_layout_response
from .sample_data import SAMPLE_TOPOLOGY, sample_initial_statuses, sample_node_ids
from .schemas import LayoutResponse, StatusResponse, TopologyIn
from .status_simulator import StatusSimulator

STATUS_TICK_SECONDS = 4
STATUS_FLIP_PROBABILITY = 0.12

status_simulator = StatusSimulator(
    node_ids=sample_node_ids(),
    initial_statuses=sample_initial_statuses(),
)


async def _status_tick_loop() -> None:
    while True:
        await asyncio.sleep(STATUS_TICK_SECONDS)
        status_simulator.tick(flip_probability=STATUS_FLIP_PROBABILITY)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_status_tick_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="InfraTopologyDashboard API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/topology/layout", response_model=LayoutResponse)
def get_sample_layout():
    return build_layout_response(SAMPLE_TOPOLOGY)


@app.post("/api/v1/topology/layout", response_model=LayoutResponse)
def post_layout(topology: TopologyIn):
    try:
        return build_layout_response(topology)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/v1/topology/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(statuses=status_simulator.snapshot(), tick=status_simulator.tick_count)
