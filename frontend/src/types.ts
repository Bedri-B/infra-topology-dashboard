// Shapes mirrored from the FastAPI backend's Pydantic schemas
// (backend/app/schemas.py). Kept as plain interfaces -- no runtime
// validation on the frontend, the backend is the source of truth.

export type NodeKind = "host" | "vm" | "service";
export type NodeStatus = "up" | "warn" | "down";
export type EdgeKind = "hosts" | "runs" | "depends_on";

export interface TopologyNode {
  id: string;
  label: string;
  kind: NodeKind;
  status: NodeStatus;
  x: number;
  y: number;
  parent: string | null;
  region: string | null;
  port: number | null;
  degree: number;
}

export interface TopologyEdge {
  source: string;
  target: string;
  kind: EdgeKind;
}

export interface Canvas {
  width: number;
  height: number;
}

export interface LayoutResponse {
  canvas: Canvas;
  seed: number;
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export interface StatusResponse {
  statuses: Record<string, NodeStatus>;
  tick: number;
}

// Ad-hoc topology input for POST /api/v1/topology/layout.
export interface HostInput {
  id: string;
  label: string;
  status?: NodeStatus;
  region?: string | null;
}

export interface VMInput {
  id: string;
  label: string;
  host_id: string;
  status?: NodeStatus;
}

export interface ServiceInput {
  id: string;
  label: string;
  vm_id: string;
  status?: NodeStatus;
  port?: number | null;
}

export interface EdgeInput {
  source: string;
  target: string;
  kind?: EdgeKind;
}

export interface TopologyInput {
  hosts: HostInput[];
  vms: VMInput[];
  services: ServiceInput[];
  edges: EdgeInput[];
}
