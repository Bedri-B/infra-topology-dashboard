import { useCallback, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent } from "react";
import type { EdgeKind, LayoutResponse, NodeKind, NodeStatus, TopologyNode } from "./types";
import { statusToColor, statusToLabel } from "./statusColor";
import { nodeRadius } from "./topologyTransform";

// Hand-rolled SVG rendering: node positions and the canvas size come
// straight from the backend's NetworkX layout, this component just draws
// them. No D3, no client-side force simulation -- pan/zoom below is plain
// viewBox arithmetic.

const EDGE_STYLE: Record<EdgeKind, { stroke: string; dash?: string; width: number; opacity: number }> = {
  hosts: { stroke: "#5b6478", width: 2, opacity: 0.55 },
  runs: { stroke: "#5b6478", width: 1.5, opacity: 0.45 },
  depends_on: { stroke: "#6c8cff", dash: "5,4", width: 1.5, opacity: 0.75 },
};

const EDGE_KIND_LABEL: Record<EdgeKind, string> = {
  hosts: "hosts",
  runs: "runs",
  depends_on: "depends on",
};

const NODE_KIND_LABEL: Record<NodeKind, string> = {
  host: "Host",
  vm: "VM",
  service: "Service",
};

const LABEL_OFFSET: Record<NodeKind, number> = {
  host: 34,
  vm: 30,
  service: 22,
};

const STATUS_ORDER: NodeStatus[] = ["up", "warn", "down"];
const NODE_KIND_ORDER: NodeKind[] = ["host", "vm", "service"];
const EDGE_KIND_ORDER: EdgeKind[] = ["hosts", "runs", "depends_on"];

interface ViewBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function NodeShape({ node }: { node: TopologyNode }) {
  const r = nodeRadius(node.kind);
  const color = statusToColor(node.status);
  const fill = "#161c2c";
  const strokeWidth = 2.5;

  if (node.kind === "host") {
    return (
      <rect
        x={node.x - r}
        y={node.y - r}
        width={r * 2}
        height={r * 2}
        rx={6}
        fill={fill}
        stroke={color}
        strokeWidth={strokeWidth}
      />
    );
  }
  if (node.kind === "vm") {
    const half = r;
    return (
      <rect
        x={node.x - half}
        y={node.y - half}
        width={half * 2}
        height={half * 2}
        transform={`rotate(45 ${node.x} ${node.y})`}
        fill={fill}
        stroke={color}
        strokeWidth={strokeWidth}
      />
    );
  }
  return <circle cx={node.x} cy={node.y} r={r} fill={fill} stroke={color} strokeWidth={strokeWidth} />;
}

export default function TopologyView({ data }: { data: LayoutResponse }) {
  const { canvas, nodes, edges } = data;
  const nodeById = new Map(nodes.map((n) => [n.id, n]));

  const initialViewBox: ViewBox = { x: 0, y: 0, w: canvas.width, h: canvas.height };
  const [viewBox, setViewBox] = useState<ViewBox>(initialViewBox);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const dragRef = useRef<{ startX: number; startY: number; origin: ViewBox } | null>(null);

  const zoom = useCallback(
    (factor: number) => {
      setViewBox((vb) => {
        const newW = clamp(vb.w * factor, canvas.width * 0.3, canvas.width * 2.2);
        const newH = clamp(vb.h * factor, canvas.height * 0.3, canvas.height * 2.2);
        return {
          x: vb.x + (vb.w - newW) / 2,
          y: vb.y + (vb.h - newH) / 2,
          w: newW,
          h: newH,
        };
      });
    },
    [canvas.width, canvas.height],
  );

  function handlePointerDown(e: ReactPointerEvent<SVGSVGElement>) {
    svgRef.current?.setPointerCapture(e.pointerId);
    dragRef.current = { startX: e.clientX, startY: e.clientY, origin: viewBox };
  }

  function handlePointerMove(e: ReactPointerEvent<SVGSVGElement>) {
    const drag = dragRef.current;
    const svg = svgRef.current;
    if (!drag || !svg) return;
    const rect = svg.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const scaleX = drag.origin.w / rect.width;
    const scaleY = drag.origin.h / rect.height;
    const dx = (e.clientX - drag.startX) * scaleX;
    const dy = (e.clientY - drag.startY) * scaleY;
    setViewBox({ ...drag.origin, x: drag.origin.x - dx, y: drag.origin.y - dy });
  }

  function handlePointerUp(e: ReactPointerEvent<SVGSVGElement>) {
    if (svgRef.current?.hasPointerCapture(e.pointerId)) {
      svgRef.current.releasePointerCapture(e.pointerId);
    }
    dragRef.current = null;
  }

  function resetView() {
    setViewBox(initialViewBox);
  }

  return (
    <div className="topology-panel">
      <div className="topology-toolbar">
        <div className="toolbar-hint">Drag to pan</div>
        <div className="toolbar-buttons">
          <button type="button" className="btn btn-icon" onClick={() => zoom(0.85)} aria-label="Zoom in">
            +
          </button>
          <button type="button" className="btn btn-icon" onClick={() => zoom(1 / 0.85)} aria-label="Zoom out">
            &minus;
          </button>
          <button type="button" className="btn btn-secondary" onClick={resetView}>
            Reset view
          </button>
        </div>
      </div>

      <svg
        ref={svgRef}
        className="topology-svg"
        viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
        role="img"
        aria-label="Infrastructure topology graph"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      >
        <g className="edges">
          {edges.map((edge) => {
            const source = nodeById.get(edge.source);
            const target = nodeById.get(edge.target);
            if (!source || !target) return null;
            const style = EDGE_STYLE[edge.kind];
            return (
              <line
                key={`${edge.source}-${edge.target}-${edge.kind}`}
                x1={source.x}
                y1={source.y}
                x2={target.x}
                y2={target.y}
                stroke={style.stroke}
                strokeWidth={style.width}
                strokeOpacity={style.opacity}
                strokeDasharray={style.dash}
              />
            );
          })}
        </g>

        <g className="nodes">
          {nodes.map((node) => (
            <g key={node.id}>
              <NodeShape node={node} />
              <text
                x={node.x}
                y={node.y + LABEL_OFFSET[node.kind]}
                textAnchor="middle"
                className="node-label"
              >
                {node.label}
              </text>
            </g>
          ))}
        </g>
      </svg>

      <div className="legend">
        <div className="legend-group">
          <span className="legend-title">Status</span>
          <div className="legend-chips">
            {STATUS_ORDER.map((status) => (
              <span key={status} className="legend-chip">
                <span className="legend-swatch" style={{ background: statusToColor(status) }} />
                {statusToLabel(status)}
              </span>
            ))}
          </div>
        </div>
        <div className="legend-group">
          <span className="legend-title">Node kind</span>
          <div className="legend-chips">
            {NODE_KIND_ORDER.map((kind) => (
              <span key={kind} className={`legend-chip legend-shape legend-shape-${kind}`}>
                <span className="legend-shape-icon" aria-hidden="true" />
                {NODE_KIND_LABEL[kind]}
              </span>
            ))}
          </div>
        </div>
        <div className="legend-group">
          <span className="legend-title">Edges</span>
          <div className="legend-chips">
            {EDGE_KIND_ORDER.map((kind) => (
              <span key={kind} className="legend-chip">
                <span
                  className="legend-line"
                  style={{
                    background: EDGE_STYLE[kind].dash ? "transparent" : EDGE_STYLE[kind].stroke,
                    borderTop: EDGE_STYLE[kind].dash
                      ? `2px dashed ${EDGE_STYLE[kind].stroke}`
                      : undefined,
                  }}
                />
                {EDGE_KIND_LABEL[kind]}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
