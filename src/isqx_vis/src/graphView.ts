import type { GraphLink, GraphNode, NodeIndex } from "./types";
import { niceName, wrapText } from "./utils";

export const LABEL_LINE_HEIGHT = 1.1; // em
const LABEL_CHAR_WIDTH = 0.62; // em
const LABEL_HORIZONTAL_PADDING = 0.75; // em
const LABEL_VERTICAL_PADDING = 0.45; // em
const LABEL_GRID_SIZE = 64;

export type WrappedNodeLabel = {
  lines: string[];
  lineCount: number;
  longestLineLength: number;
  startYOffset: number;
};

export type GraphNodeViewState = {
  isActive: boolean;
  isDimmed: boolean;
  isHighlighted: boolean;
  isSelected: boolean;
  showLabel: boolean;
};

type LabelBounds = {
  left: number;
  top: number;
  right: number;
  bottom: number;
};

type LabelCandidate = {
  index: number;
  priority: number;
  radius: number;
  value: number;
  bounds: LabelBounds;
};

export const hasFocus = (
  selectedNodeIndices: NodeIndex[],
  highlightedNodeIndex: NodeIndex | null
) => selectedNodeIndices.length > 0 || highlightedNodeIndex !== null;

export const getFocusedNodeIndex = (
  selectedNodeIndices: NodeIndex[],
  highlightedNodeIndex: NodeIndex | null
) => {
  if (highlightedNodeIndex !== null) return highlightedNodeIndex;
  return selectedNodeIndices.length === 1 ? selectedNodeIndices[0] : null;
};

const getFocusIndexSet = (
  selectedNodeIndices: NodeIndex[],
  highlightedNodeIndex: NodeIndex | null
) => {
  const focusIndices = new Set(selectedNodeIndices);
  if (highlightedNodeIndex !== null) {
    focusIndices.add(highlightedNodeIndex);
  }
  return focusIndices;
};

export const getActiveLinks = (
  selectedNodeIndices: NodeIndex[],
  highlightedNodeIndex: NodeIndex | null,
  linkMap: Map<number, GraphLink[]>
) => {
  if (!hasFocus(selectedNodeIndices, highlightedNodeIndex)) {
    return [];
  }

  const linksToShow = new Set<GraphLink>();
  for (const index of getFocusIndexSet(
    selectedNodeIndices,
    highlightedNodeIndex
  )) {
    const links = linkMap.get(index);
    if (!links) continue;
    for (const link of links) {
      linksToShow.add(link);
    }
  }

  return [...linksToShow];
};

export const getActiveNodeIndexSet = (
  selectedNodeIndices: NodeIndex[],
  highlightedNodeIndex: NodeIndex | null,
  linkMap: Map<number, GraphLink[]>
) => {
  if (!hasFocus(selectedNodeIndices, highlightedNodeIndex)) {
    return new Set<number>();
  }

  const focusIndices = getFocusIndexSet(
    selectedNodeIndices,
    highlightedNodeIndex
  );
  const active = new Set(focusIndices);

  for (const index of focusIndices) {
    const links = linkMap.get(index);
    if (!links) continue;
    for (const link of links) {
      active.add(link.source);
      active.add(link.target);
    }
  }

  return active;
};

export const getWrappedNodeLabels = (nodes: GraphNode[]) => {
  return nodes.map(node => {
    const lines = wrapText(niceName(node.publicApiPath));
    return {
      lines,
      lineCount: lines.length,
      longestLineLength: lines.reduce(
        (longest, line) => Math.max(longest, line.length),
        0
      ),
      startYOffset: -((lines.length - 1) * LABEL_LINE_HEIGHT) / 2
    } satisfies WrappedNodeLabel;
  });
};

export const isNodeLabelLegible = (node: GraphNode, zoomScale: number) => {
  const screenRadius = node.radius * zoomScale;
  return screenRadius > 36 && screenRadius < 224;
};

export const getVisibleLabelIndices = ({
  nodes,
  labels,
  activeNodeIndices,
  selectedNodeIndices,
  highlightedNodeIndex,
  focusActive,
  zoomScale
}: {
  nodes: GraphNode[];
  labels: WrappedNodeLabel[];
  activeNodeIndices: Set<number>;
  selectedNodeIndices: Set<number>;
  highlightedNodeIndex: NodeIndex | null;
  focusActive: boolean;
  zoomScale: number;
}) => {
  const candidates: LabelCandidate[] = [];

  for (let index = 0; index < nodes.length; index++) {
    const node = nodes[index];
    const label = labels[index];
    const isHighlighted = highlightedNodeIndex === index;
    const isSelected = selectedNodeIndices.has(index);
    const isPriority = isHighlighted || isSelected;
    const isEligible = focusActive
      ? activeNodeIndices.has(index)
      : isNodeLabelLegible(node, zoomScale);

    if (!label || (!isEligible && !isPriority)) continue;

    candidates.push({
      index,
      priority: isHighlighted ? 0 : isSelected ? 1 : focusActive ? 2 : 3,
      radius: node.radius,
      value: node.value,
      bounds: getLabelBounds(node, label)
    });
  }

  candidates.sort((a, b) => {
    if (a.priority !== b.priority) return a.priority - b.priority;
    if (a.radius !== b.radius) return b.radius - a.radius;
    if (a.value !== b.value) return b.value - a.value;
    return a.index - b.index;
  });

  const visible = new Set<number>();
  const grid = new Map<string, LabelBounds[]>();

  for (const candidate of candidates) {
    const forceVisible = candidate.priority <= 1;
    if (forceVisible || !gridHasOverlap(grid, candidate.bounds)) {
      visible.add(candidate.index);
      gridInsert(grid, candidate.bounds);
    }
  }

  return visible;
};

export const getNodeViewStates = ({
  nodes,
  activeNodeIndices,
  selectedNodeIndices,
  highlightedNodeIndex,
  focusActive,
  visibleLabelIndices
}: {
  nodes: GraphNode[];
  activeNodeIndices: Set<number>;
  selectedNodeIndices: Set<number>;
  highlightedNodeIndex: NodeIndex | null;
  focusActive: boolean;
  visibleLabelIndices: Set<number>;
}) => {
  return nodes.map((_, index) => {
    const isSelected = selectedNodeIndices.has(index);
    const isHighlighted = highlightedNodeIndex === index;
    const isActive = activeNodeIndices.has(index);

    return {
      isActive,
      isDimmed: focusActive && !isActive,
      isHighlighted,
      isSelected,
      showLabel: visibleLabelIndices.has(index)
    } satisfies GraphNodeViewState;
  });
};

const getLabelBounds = (
  node: GraphNode,
  label: WrappedNodeLabel
): LabelBounds => {
  const fontSize = Math.max(3, node.radius / 3);
  const halfWidth =
    ((label.longestLineLength * LABEL_CHAR_WIDTH) / 2 +
      LABEL_HORIZONTAL_PADDING) *
    fontSize;
  const halfHeight =
    ((label.lineCount * LABEL_LINE_HEIGHT) / 2 + LABEL_VERTICAL_PADDING) *
    fontSize;

  return {
    left: node.x - halfWidth,
    right: node.x + halfWidth,
    top: node.y - halfHeight,
    bottom: node.y + halfHeight
  };
};

const gridCellKey = (x: number, y: number) => `${x},${y}`;

const forEachGridCell = (bounds: LabelBounds, visit: (key: string) => void) => {
  const minX = Math.floor(bounds.left / LABEL_GRID_SIZE);
  const maxX = Math.floor(bounds.right / LABEL_GRID_SIZE);
  const minY = Math.floor(bounds.top / LABEL_GRID_SIZE);
  const maxY = Math.floor(bounds.bottom / LABEL_GRID_SIZE);

  for (let x = minX; x <= maxX; x++) {
    for (let y = minY; y <= maxY; y++) {
      visit(gridCellKey(x, y));
    }
  }
};

const overlaps = (a: LabelBounds, b: LabelBounds) =>
  a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;

const gridHasOverlap = (
  grid: Map<string, LabelBounds[]>,
  bounds: LabelBounds
) => {
  let didOverlap = false;

  forEachGridCell(bounds, key => {
    if (didOverlap) return;
    const bucket = grid.get(key);
    if (!bucket) return;

    for (const other of bucket) {
      if (overlaps(bounds, other)) {
        didOverlap = true;
        return;
      }
    }
  });

  return didOverlap;
};

const gridInsert = (grid: Map<string, LabelBounds[]>, bounds: LabelBounds) => {
  forEachGridCell(bounds, key => {
    const bucket = grid.get(key);
    if (bucket) {
      bucket.push(bounds);
    } else {
      grid.set(key, [bounds]);
    }
  });
};
