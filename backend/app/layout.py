"""Fixed-seed force-directed layout for infrastructure topology graphs.

Given hosts, VMs, services and edges, this module builds a NetworkX graph
(containment edges generated from host_id/vm_id references, plus whatever
explicit dependency edges were supplied) and computes (x, y) node positions
with a seeded spring layout, normalized into a fixed canvas so the frontend
can render them directly with no client-side layout math.

Determinism matters here the same way it does for a dependency graph or an
org chart: reloading the dashboard, or diffing two runs in CI, should show
the same shape every time for the same topology. `LAYOUT_SEED` pins the
spring layout's random initial placement.
"""

import networkx as nx

from .schemas import TopologyIn

LAYOUT_SEED = 42
CANVAS_WIDTH = 960
CANVAS_HEIGHT = 640
CANVAS_PADDING = 60

# Containment edges (host->vm, vm->service) pull their endpoints tightly
# together during layout; explicit dependency edges are a looser pull so a
# service's dependencies fan out around it instead of collapsing onto it.
EDGE_LAYOUT_WEIGHT = {
    "hosts": 1.0,
    "runs": 1.0,
    "depends_on": 0.35,
}

STATUS_RANK = {"up": 0, "warn": 1, "down": 2}


def build_graph(topology: TopologyIn) -> nx.Graph:
    """Build a typed NetworkX graph from a validated TopologyIn.

    Every node carries `kind` (host/vm/service), `label`, `status`, and an
    optional `parent` (the host a VM sits on, or the VM a service runs in).
    Containment edges are synthesized from host_id/vm_id; anything in
    `topology.edges` is added on top of that.
    """
    graph = nx.Graph()

    for host in topology.hosts:
        graph.add_node(
            host.id, kind="host", label=host.label, status=host.status,
            parent=None, region=host.region, port=None,
        )
    for vm in topology.vms:
        graph.add_node(
            vm.id, kind="vm", label=vm.label, status=vm.status,
            parent=vm.host_id, region=None, port=None,
        )
        graph.add_edge(vm.host_id, vm.id, kind="hosts", weight=EDGE_LAYOUT_WEIGHT["hosts"])
    for service in topology.services:
        graph.add_node(
            service.id, kind="service", label=service.label, status=service.status,
            parent=service.vm_id, region=None, port=service.port,
        )
        graph.add_edge(service.vm_id, service.id, kind="runs", weight=EDGE_LAYOUT_WEIGHT["runs"])

    for edge in topology.edges:
        graph.add_edge(
            edge.source, edge.target, kind=edge.kind,
            weight=EDGE_LAYOUT_WEIGHT.get(edge.kind, 0.5),
        )

    return graph


def _normalize_positions(pos: dict) -> dict:
    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = (max_x - min_x) or 1.0
    span_y = (max_y - min_y) or 1.0

    usable_w = CANVAS_WIDTH - 2 * CANVAS_PADDING
    usable_h = CANVAS_HEIGHT - 2 * CANVAS_PADDING

    normalized = {}
    for node, (x, y) in pos.items():
        nx_ = CANVAS_PADDING + (x - min_x) / span_x * usable_w
        ny_ = CANVAS_PADDING + (y - min_y) / span_y * usable_h
        normalized[node] = (round(nx_, 2), round(ny_, 2))
    return normalized


def compute_layout(graph: nx.Graph, seed: int = LAYOUT_SEED) -> dict:
    """Fixed-seed force-directed (x, y) per node, normalized to the canvas."""
    if graph.number_of_nodes() == 0:
        return {}
    if graph.number_of_nodes() == 1:
        (only_node,) = graph.nodes
        return {only_node: (CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)}
    pos = nx.spring_layout(graph, seed=seed, weight="weight", k=None)
    return _normalize_positions(pos)


def build_layout_response(topology: TopologyIn, seed: int = LAYOUT_SEED) -> dict:
    graph = build_graph(topology)
    positions = compute_layout(graph, seed=seed)
    degrees = dict(graph.degree())

    nodes = []
    for node_id, data in graph.nodes(data=True):
        x, y = positions[node_id]
        nodes.append({
            "id": node_id,
            "label": data["label"],
            "kind": data["kind"],
            "status": data["status"],
            "x": x,
            "y": y,
            "parent": data["parent"],
            "region": data["region"],
            "port": data["port"],
            "degree": degrees[node_id],
        })
    # Stable order: by kind (host, vm, service) then id, so the same topology
    # always serializes the same way regardless of dict insertion order.
    kind_rank = {"host": 0, "vm": 1, "service": 2}
    nodes.sort(key=lambda n: (kind_rank[n["kind"]], n["id"]))

    edges = [
        {"source": u, "target": v, "kind": data["kind"]}
        for u, v, data in graph.edges(data=True)
    ]
    edges.sort(key=lambda e: (e["source"], e["target"]))

    return {
        "canvas": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT},
        "seed": seed,
        "nodes": nodes,
        "edges": edges,
    }
