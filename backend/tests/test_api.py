from fastapi.testclient import TestClient

from app.main import app
from app.status_simulator import STATUSES

client = TestClient(app)


class TestLayoutEndpoint:
    def test_get_returns_sample_topology_layout(self):
        response = client.get("/api/v1/topology/layout")
        assert response.status_code == 200
        body = response.json()
        assert len(body["nodes"]) == 11
        assert body["seed"] == 42

    def test_post_accepts_custom_topology(self):
        payload = {
            "hosts": [{"id": "h1", "label": "h1", "status": "up"}],
            "vms": [{"id": "v1", "label": "v1", "host_id": "h1", "status": "up"}],
            "services": [{"id": "s1", "label": "s1", "vm_id": "v1", "status": "down"}],
            "edges": [],
        }
        response = client.post("/api/v1/topology/layout", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert len(body["nodes"]) == 3
        statuses = {n["id"]: n["status"] for n in body["nodes"]}
        assert statuses["s1"] == "down"

    def test_post_rejects_vm_with_unknown_host(self):
        payload = {
            "hosts": [{"id": "h1", "label": "h1"}],
            "vms": [{"id": "v1", "label": "v1", "host_id": "does-not-exist"}],
            "services": [],
            "edges": [],
        }
        response = client.post("/api/v1/topology/layout", json=payload)
        assert response.status_code == 422

    def test_post_rejects_duplicate_ids(self):
        payload = {
            "hosts": [{"id": "dupe", "label": "h1"}],
            "vms": [{"id": "dupe", "label": "v1", "host_id": "dupe"}],
            "services": [],
            "edges": [],
        }
        response = client.post("/api/v1/topology/layout", json=payload)
        assert response.status_code == 422


class TestStatusEndpoint:
    def test_returns_a_status_for_every_sample_node(self):
        response = client.get("/api/v1/topology/status")
        assert response.status_code == 200
        body = response.json()
        layout_body = client.get("/api/v1/topology/layout").json()
        layout_ids = {n["id"] for n in layout_body["nodes"]}
        assert set(body["statuses"].keys()) == layout_ids

    def test_all_statuses_are_valid_values(self):
        response = client.get("/api/v1/topology/status")
        body = response.json()
        assert all(status in STATUSES for status in body["statuses"].values())


class TestHealthEndpoint:
    def test_health_ok(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
