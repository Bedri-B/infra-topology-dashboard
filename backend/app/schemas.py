"""Pydantic schemas for the topology API.

The input contract is deliberately three flat lists (hosts / vms / services)
plus an explicit edge list, mirroring how infrastructure is usually described:
physical or cloud hosts, the VMs that run on them, and the services that run
inside those VMs. Containment ("host runs vm", "vm runs service") is implied
by `host_id` / `vm_id` references and turned into graph edges automatically;
the `edges` list is for everything else -- service-to-service dependencies,
cross-host calls, load balancer fan-out, etc.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

NodeStatus = Literal["up", "warn", "down"]
EdgeKind = Literal["hosts", "runs", "depends_on"]


class HostIn(BaseModel):
    id: str
    label: str
    status: NodeStatus = "up"
    region: str | None = None


class VMIn(BaseModel):
    id: str
    label: str
    host_id: str
    status: NodeStatus = "up"


class ServiceIn(BaseModel):
    id: str
    label: str
    vm_id: str
    status: NodeStatus = "up"
    port: int | None = None


class EdgeIn(BaseModel):
    source: str
    target: str
    kind: EdgeKind = "depends_on"


class TopologyIn(BaseModel):
    hosts: list[HostIn] = Field(default_factory=list)
    vms: list[VMIn] = Field(default_factory=list)
    services: list[ServiceIn] = Field(default_factory=list)
    edges: list[EdgeIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_references(self) -> "TopologyIn":
        host_ids = {h.id for h in self.hosts}
        vm_ids = {v.id for v in self.vms}
        all_ids = host_ids | vm_ids | {s.id for s in self.services}

        dupes = _find_duplicates(
            [h.id for h in self.hosts] + [v.id for v in self.vms] + [s.id for s in self.services]
        )
        if dupes:
            raise ValueError(f"Duplicate node id(s) across hosts/vms/services: {sorted(dupes)}")

        for vm in self.vms:
            if vm.host_id not in host_ids:
                raise ValueError(f"VM '{vm.id}' references unknown host_id '{vm.host_id}'")
        for service in self.services:
            if service.vm_id not in vm_ids:
                raise ValueError(f"Service '{service.id}' references unknown vm_id '{service.vm_id}'")
        for edge in self.edges:
            if edge.source not in all_ids or edge.target not in all_ids:
                raise ValueError(
                    f"Edge {edge.source} -> {edge.target} references a node id not present "
                    "in hosts/vms/services"
                )
        return self


def _find_duplicates(ids: list[str]) -> set[str]:
    seen: set[str] = set()
    dupes: set[str] = set()
    for node_id in ids:
        if node_id in seen:
            dupes.add(node_id)
        seen.add(node_id)
    return dupes


class LayoutNode(BaseModel):
    id: str
    label: str
    kind: Literal["host", "vm", "service"]
    status: NodeStatus
    x: float
    y: float
    parent: str | None = None
    region: str | None = None
    port: int | None = None
    degree: int


class LayoutEdge(BaseModel):
    source: str
    target: str
    kind: EdgeKind


class LayoutResponse(BaseModel):
    canvas: dict[str, int]
    seed: int
    nodes: list[LayoutNode]
    edges: list[LayoutEdge]


class StatusResponse(BaseModel):
    statuses: dict[str, NodeStatus]
    tick: int
