"""Bundled sample topology.

Entirely made up: generic hostnames, no real infrastructure, IPs, or
provider details. Two web hosts behind a shared Postgres/Redis host, each
running one VM, each VM running a couple of services -- enough shape to
show off containment (host -> vm -> service) plus explicit dependency
edges (service -> service) in one small graph.
"""

from .schemas import EdgeIn, HostIn, ServiceIn, TopologyIn, VMIn

SAMPLE_TOPOLOGY = TopologyIn(
    hosts=[
        HostIn(id="host-web-01", label="web-01", status="up", region="us-east"),
        HostIn(id="host-web-02", label="web-02", status="up", region="us-east"),
        HostIn(id="host-db-01", label="db-01", status="up", region="us-east"),
    ],
    vms=[
        VMIn(id="vm-web-01a", label="web-01-vm-a", host_id="host-web-01", status="up"),
        VMIn(id="vm-web-02a", label="web-02-vm-a", host_id="host-web-02", status="up"),
        VMIn(id="vm-db-01a", label="db-01-vm-a", host_id="host-db-01", status="up"),
    ],
    services=[
        ServiceIn(id="svc-api-1", label="api", vm_id="vm-web-01a", status="up", port=8080),
        ServiceIn(id="svc-api-2", label="api", vm_id="vm-web-02a", status="up", port=8080),
        ServiceIn(id="svc-worker", label="worker", vm_id="vm-web-01a", status="warn", port=None),
        ServiceIn(id="svc-postgres", label="postgres", vm_id="vm-db-01a", status="up", port=5432),
        ServiceIn(id="svc-redis", label="redis", vm_id="vm-db-01a", status="up", port=6379),
    ],
    edges=[
        EdgeIn(source="svc-api-1", target="svc-postgres", kind="depends_on"),
        EdgeIn(source="svc-api-2", target="svc-postgres", kind="depends_on"),
        EdgeIn(source="svc-api-1", target="svc-redis", kind="depends_on"),
        EdgeIn(source="svc-api-2", target="svc-redis", kind="depends_on"),
        EdgeIn(source="svc-worker", target="svc-postgres", kind="depends_on"),
        EdgeIn(source="svc-worker", target="svc-redis", kind="depends_on"),
    ],
)


def sample_node_ids() -> list[str]:
    return (
        [h.id for h in SAMPLE_TOPOLOGY.hosts]
        + [v.id for v in SAMPLE_TOPOLOGY.vms]
        + [s.id for s in SAMPLE_TOPOLOGY.services]
    )


def sample_initial_statuses() -> dict[str, str]:
    statuses: dict[str, str] = {}
    for host in SAMPLE_TOPOLOGY.hosts:
        statuses[host.id] = host.status
    for vm in SAMPLE_TOPOLOGY.vms:
        statuses[vm.id] = vm.status
    for service in SAMPLE_TOPOLOGY.services:
        statuses[service.id] = service.status
    return statuses
