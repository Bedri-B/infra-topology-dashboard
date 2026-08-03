// Pure, DOM-free helpers for turning a layout response + a live status
// snapshot into render-ready data. No React, no fetch -- easy to unit test.

import type { NodeKind, NodeStatus, TopologyNode } from "./types";

/**
 * Overlay a live status snapshot (from GET /api/v1/topology/status) onto a
 * node list from the layout response. Nodes not present in `statuses` (or
 * whose status hasn't changed) are returned unchanged so React can bail out
 * of re-rendering them via reference equality.
 */
export function mergeNodeStatuses(
  nodes: TopologyNode[],
  statuses: Record<string, NodeStatus>,
): TopologyNode[] {
  return nodes.map((node) => {
    const live = statuses[node.id];
    if (!live || live === node.status) return node;
    return { ...node, status: live };
  });
}

const NODE_RADIUS: Record<NodeKind, number> = {
  host: 20,
  vm: 15,
  service: 10,
};

export function nodeRadius(kind: NodeKind): number {
  return NODE_RADIUS[kind];
}

export function groupNodesByKind(nodes: TopologyNode[]): Record<NodeKind, TopologyNode[]> {
  const groups: Record<NodeKind, TopologyNode[]> = { host: [], vm: [], service: [] };
  for (const node of nodes) {
    groups[node.kind].push(node);
  }
  return groups;
}

export function countByStatus(nodes: TopologyNode[]): Record<NodeStatus, number> {
  const counts: Record<NodeStatus, number> = { up: 0, warn: 0, down: 0 };
  for (const node of nodes) {
    counts[node.status] += 1;
  }
  return counts;
}
