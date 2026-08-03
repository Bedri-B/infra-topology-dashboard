// Pure status -> visual mapping. Kept framework-free so it unit tests
// without touching React or the DOM.

import type { NodeStatus } from "./types";

export const STATUS_COLOR: Record<NodeStatus, string> = {
  up: "#2f9e44",
  warn: "#f5a623",
  down: "#e03131",
};

export const STATUS_LABEL: Record<NodeStatus, string> = {
  up: "Up",
  warn: "Degraded",
  down: "Down",
};

const STATUS_SEVERITY: Record<NodeStatus, number> = {
  up: 0,
  warn: 1,
  down: 2,
};

export function statusToColor(status: NodeStatus): string {
  return STATUS_COLOR[status];
}

export function statusToLabel(status: NodeStatus): string {
  return STATUS_LABEL[status];
}

/** Higher-severity status wins (down > warn > up). */
export function worseStatus(a: NodeStatus, b: NodeStatus): NodeStatus {
  return STATUS_SEVERITY[b] > STATUS_SEVERITY[a] ? b : a;
}

/** Worst status across a list of statuses; "up" for an empty list. */
export function worstStatus(statuses: NodeStatus[]): NodeStatus {
  return statuses.reduce<NodeStatus>((worst, status) => worseStatus(worst, status), "up");
}
