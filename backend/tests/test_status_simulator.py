import random

from app.status_simulator import STATUSES, TRANSITIONS, StatusSimulator


class TestSnapshot:
    def test_contains_every_node_id(self):
        sim = StatusSimulator(node_ids=["a", "b", "c"])
        assert set(sim.snapshot().keys()) == {"a", "b", "c"}

    def test_defaults_to_up_unless_overridden(self):
        sim = StatusSimulator(node_ids=["a", "b"], initial_statuses={"b": "down"})
        snap = sim.snapshot()
        assert snap["a"] == "up"
        assert snap["b"] == "down"

    def test_snapshot_is_a_copy(self):
        sim = StatusSimulator(node_ids=["a"])
        snap = sim.snapshot()
        snap["a"] = "down"
        assert sim.snapshot()["a"] == "up"


class TestTick:
    def test_zero_probability_never_changes_anything(self):
        sim = StatusSimulator(node_ids=["a", "b", "c"], rng=random.Random(1))
        before = sim.snapshot()
        for _ in range(20):
            sim.tick(flip_probability=0.0)
        assert sim.snapshot() == before

    def test_tick_count_increments(self):
        sim = StatusSimulator(node_ids=["a"])
        assert sim.tick_count == 0
        sim.tick(flip_probability=0.0)
        sim.tick(flip_probability=0.0)
        assert sim.tick_count == 2

    def test_statuses_always_stay_valid(self):
        sim = StatusSimulator(node_ids=[f"node-{i}" for i in range(10)], rng=random.Random(7))
        for _ in range(200):
            snapshot = sim.tick(flip_probability=0.5)
        assert all(status in STATUSES for status in snapshot.values())

    def test_deterministic_given_same_seed(self):
        sim_a = StatusSimulator(node_ids=["a", "b", "c", "d"], rng=random.Random(42))
        sim_b = StatusSimulator(node_ids=["a", "b", "c", "d"], rng=random.Random(42))
        for _ in range(15):
            snap_a = sim_a.tick(flip_probability=0.3)
            snap_b = sim_b.tick(flip_probability=0.3)
            assert snap_a == snap_b

    def test_different_seeds_can_diverge(self):
        sim_a = StatusSimulator(node_ids=[f"n{i}" for i in range(20)], rng=random.Random(1))
        sim_b = StatusSimulator(node_ids=[f"n{i}" for i in range(20)], rng=random.Random(2))
        for _ in range(10):
            snap_a = sim_a.tick(flip_probability=0.5)
            snap_b = sim_b.tick(flip_probability=0.5)
        assert snap_a != snap_b

    def test_high_probability_actually_moves_statuses_over_time(self):
        # Not every individual tick has to change things, but over many
        # ticks at flip_probability=1.0 a node can't stay "up" forever if
        # up->up is < 1.0 in the transition matrix.
        sim = StatusSimulator(node_ids=["a"], rng=random.Random(3))
        seen = set()
        for _ in range(50):
            seen.add(sim.tick(flip_probability=1.0)["a"])
        assert len(seen) > 1


class TestTransitionMatrix:
    def test_every_status_has_a_row(self):
        assert set(TRANSITIONS.keys()) == set(STATUSES)

    def test_rows_sum_to_one(self):
        for status, row in TRANSITIONS.items():
            assert set(row.keys()) == set(STATUSES)
            assert abs(sum(row.values()) - 1.0) < 1e-9
