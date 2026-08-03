import { describe, expect, it } from "vitest";
import { countByStatus, groupNodesByKind, mergeNodeStatuses, nodeRadius } from "./topologyTransform";
import type { TopologyNode } from "./types";

function node(overrides: Partial<TopologyNode>): TopologyNode {
  return {
    id: "n1",
    label: "n1",
    kind: "service",
    status: "up",
    x: 0,
    y: 0,
    parent: null,
    region: null,
    port: null,
    degree: 0,
    ...overrides,
  };
}

describe("mergeNodeStatuses", () => {
  it("overlays live statuses by node id", () => {
    const nodes = [node({ id: "a", status: "up" }), node({ id: "b", status: "up" })];
    const merged = mergeNodeStatuses(nodes, { a: "down" });
    expect(merged.find((n) => n.id === "a")?.status).toBe("down");
    expect(merged.find((n) => n.id === "b")?.status).toBe("up");
  });

  it("leaves nodes unchanged (same reference) when status is identical", () => {
    const nodes = [node({ id: "a", status: "up" })];
    const merged = mergeNodeStatuses(nodes, { a: "up" });
    expect(merged[0]).toBe(nodes[0]);
  });

  it("leaves nodes unchanged when missing from the status map", () => {
    const nodes = [node({ id: "a", status: "warn" })];
    const merged = mergeNodeStatuses(nodes, {});
    expect(merged[0]).toBe(nodes[0]);
  });

  it("returns a new array without mutating the input", () => {
    const nodes = [node({ id: "a", status: "up" })];
    const merged = mergeNodeStatuses(nodes, { a: "down" });
    expect(merged).not.toBe(nodes);
    expect(nodes[0].status).toBe("up");
  });
});

describe("nodeRadius", () => {
  it("orders host > vm > service so containment reads visually", () => {
    expect(nodeRadius("host")).toBeGreaterThan(nodeRadius("vm"));
    expect(nodeRadius("vm")).toBeGreaterThan(nodeRadius("service"));
  });
});

describe("groupNodesByKind", () => {
  it("buckets nodes by kind, including empty buckets", () => {
    const nodes = [node({ id: "h1", kind: "host" }), node({ id: "s1", kind: "service" })];
    const groups = groupNodesByKind(nodes);
    expect(groups.host).toHaveLength(1);
    expect(groups.service).toHaveLength(1);
    expect(groups.vm).toHaveLength(0);
  });
});

describe("countByStatus", () => {
  it("tallies nodes per status", () => {
    const nodes = [
      node({ id: "1", status: "up" }),
      node({ id: "2", status: "up" }),
      node({ id: "3", status: "warn" }),
      node({ id: "4", status: "down" }),
    ];
    expect(countByStatus(nodes)).toEqual({ up: 2, warn: 1, down: 1 });
  });

  it("returns all-zero counts for an empty list", () => {
    expect(countByStatus([])).toEqual({ up: 0, warn: 0, down: 0 });
  });
});
