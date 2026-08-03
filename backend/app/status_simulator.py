"""In-memory status simulator.

There's no real infrastructure behind this dashboard, so "live status" is
simulated: each tick, every node has a small chance of transitioning to a
new status, weighted so `up` is sticky, `warn` is a plausible middle state,
and `down` tends to recover rather than being a dead end. The frontend polls
`/api/v1/topology/status` every few seconds and the tick count changes each
time `tick()` runs, so a poller can tell whether anything actually happened.

Kept deliberately free of FastAPI/asyncio concerns so the transition logic
is trivial to unit test: seed a `random.Random` and the whole sequence of
ticks is reproducible.
"""

import random
from typing import Iterable

STATUSES = ("up", "warn", "down")

# Row = current status, values = probability of transitioning to each status
# on a tick where this node was selected to change at all. Rows sum to 1.0.
TRANSITIONS: dict[str, dict[str, float]] = {
    "up": {"up": 0.55, "warn": 0.35, "down": 0.10},
    "warn": {"up": 0.45, "warn": 0.30, "down": 0.25},
    "down": {"up": 0.55, "warn": 0.30, "down": 0.15},
}


class StatusSimulator:
    """Holds a live status map for a fixed set of node ids."""

    def __init__(
        self,
        node_ids: Iterable[str],
        initial_statuses: dict[str, str] | None = None,
        rng: random.Random | None = None,
    ):
        self._rng = rng if rng is not None else random.Random()
        initial_statuses = initial_statuses or {}
        self._statuses: dict[str, str] = {
            node_id: initial_statuses.get(node_id, "up") for node_id in node_ids
        }
        self._tick_count = 0

    @property
    def tick_count(self) -> int:
        return self._tick_count

    def snapshot(self) -> dict[str, str]:
        """Current status for every node this simulator was built with."""
        return dict(self._statuses)

    def tick(self, flip_probability: float = 0.12) -> dict[str, str]:
        """Advance the simulation by one step.

        For each node, with probability `flip_probability`, redraw its
        status from the transition matrix row for its current status
        (which can redraw the same status -- a "flip attempt" isn't
        guaranteed to change anything, matching how real health checks
        mostly reconfirm the status quo).
        """
        self._tick_count += 1
        for node_id, current in list(self._statuses.items()):
            if self._rng.random() < flip_probability:
                self._statuses[node_id] = self._weighted_next(current)
        return self.snapshot()

    def _weighted_next(self, current: str) -> str:
        row = TRANSITIONS[current]
        draw = self._rng.random()
        cumulative = 0.0
        for status in STATUSES:
            cumulative += row[status]
            if draw <= cumulative:
                return status
        return current  # pragma: no cover - unreachable when rows sum to 1.0
