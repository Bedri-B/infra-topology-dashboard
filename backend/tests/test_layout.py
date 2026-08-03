import pytest

from app.layout import CANVAS_HEIGHT, CANVAS_WIDTH, build_graph, build_layout_response, compute_layout
from app.sample_data import SAMPLE_TOPOLOGY
from app.schemas import EdgeIn, HostIn, ServiceIn, TopologyIn, VMIn

SMALL_TOPOLOGY = TopologyIn(
    hosts=[HostIn(id="h1", label="h1", status="up")],
    vms=[VMIn(id="v1", label="v1", host_id="h1", status="up")],
    services=[
        ServiceIn(id="s1", label="s1", vm_id="v1", status="up"),
        ServiceIn(id="s2", label="s2", vm_id="v1", status="warn"),
    ],
    edges=[EdgeIn(source="s1", target="s2", kind="depends_on")],
)


class TestBuildGraph:
    def test_node_count_and_kinds(self):
        graph = build_graph(SMALL_TOPOLOGY)
        assert set(graph.nodes) == {"h1", "v1", "s1", "s2"}
        assert graph.nodes["h1"]["kind"] == "host"
        assert graph.nodes["v1"]["kind"] == "vm"
        assert graph.nodes["s2"]["status"] == "warn"

    def test_containment_edges_are_synthesized(self):
        graph = build_graph(SMALL_TOPOLOGY)
        assert graph.has_edge("h1", "v1")
        assert graph["h1"]["v1"]["kind"] == "hosts"
        assert graph.has_edge("v1", "s1")
        assert graph["v1"]["s1"]["kind"] == "runs"

    def test_explicit_edge_is_included(self):
        graph = build_graph(SMALL_TOPOLOGY)
        assert graph.has_edge("s1", "s2")
        assert graph["s1"]["s2"]["kind"] == "depends_on"

    def test_sample_topology_node_count(self):
        graph = build_graph(SAMPLE_TOPOLOGY)
        # 3 hosts + 3 vms + 5 services
        assert graph.number_of_nodes() == 11


class TestComputeLayout:
    def test_deterministic_for_fixed_seed(self):
        graph = build_graph(SAMPLE_TOPOLOGY)
        first = compute_layout(graph, seed=42)
        second = compute_layout(graph, seed=42)
        assert first == second

    def test_different_seed_can_change_layout(self):
        graph = build_graph(SAMPLE_TOPOLOGY)
        a = compute_layout(graph, seed=1)
        b = compute_layout(graph, seed=2)
        assert a != b

    def test_positions_stay_within_canvas(self):
        graph = build_graph(SAMPLE_TOPOLOGY)
        positions = compute_layout(graph)
        for x, y in positions.values():
            assert 0 <= x <= CANVAS_WIDTH
            assert 0 <= y <= CANVAS_HEIGHT

    def test_single_node_graph_does_not_crash(self):
        topology = TopologyIn(hosts=[HostIn(id="only", label="only", status="up")])
        graph = build_graph(topology)
        positions = compute_layout(graph)
        assert positions == {"only": (CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)}

    def test_empty_graph_returns_empty_positions(self):
        graph = build_graph(TopologyIn())
        assert compute_layout(graph) == {}


class TestBuildLayoutResponse:
    def test_response_shape(self):
        response = build_layout_response(SMALL_TOPOLOGY)
        assert response["seed"] == 42
        assert len(response["nodes"]) == 4
        assert len(response["edges"]) == 4  # h1->v1, v1->s1, v1->s2, s1->s2
        node = response["nodes"][0]
        for field in ("id", "label", "kind", "status", "x", "y", "parent", "degree"):
            assert field in node

    def test_node_order_is_stable_across_calls(self):
        first = build_layout_response(SAMPLE_TOPOLOGY)
        second = build_layout_response(SAMPLE_TOPOLOGY)
        assert [n["id"] for n in first["nodes"]] == [n["id"] for n in second["nodes"]]

    def test_hosts_sort_before_vms_and_services(self):
        response = build_layout_response(SAMPLE_TOPOLOGY)
        kinds = [n["kind"] for n in response["nodes"]]
        assert kinds.index("host") < kinds.index("vm") < kinds.index("service")


@pytest.mark.parametrize("bad_edge_target", ["missing-node"])
def test_topology_rejects_edge_to_unknown_node(bad_edge_target):
    with pytest.raises(ValueError):
        TopologyIn(
            hosts=[HostIn(id="h1", label="h1")],
            edges=[EdgeIn(source="h1", target=bad_edge_target)],
        )
