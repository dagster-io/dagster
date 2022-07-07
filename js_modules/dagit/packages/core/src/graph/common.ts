import {AssetGraphLayout, AssetLayout} from '../asset-graph/layout';

import {OpGraphLayout, OpLayout} from './layout';

export type Edge = {a: string; b: string};

export type IBounds = {
  x: number;
  y: number;
  height: number;
  width: number;
};

export type IPoint = {
  x: number;
  y: number;
};

export const isHighlighted = (edges: Edge[], {a, b}: Edge) =>
  edges.some((h) => (h.a === a && h.b === b) || (h.b === a && h.a === b));

export const isOpHighlighted = (edges: Edge[], name: string) =>
  edges.some((h) => h.a.split(':')[0] === name || h.b.split(':')[0] === name);

export const isNodeOffscreen = (
  layoutNode: {x: number; y: number; width: number; height: number},
  viewportRect: {top: number; left: number; right: number; bottom: number},
) => {
  return (
    layoutNode.x + layoutNode.width < viewportRect.left ||
    layoutNode.y + layoutNode.height < viewportRect.top ||
    layoutNode.x > viewportRect.right ||
    layoutNode.y > viewportRect.bottom
  );
};

export const closestNodeInDirection = (
  layout: OpGraphLayout | AssetGraphLayout,
  selectedNodeKey: string | undefined,
  dir: string,
): string | undefined => {
  if (!selectedNodeKey) {
    return;
  }

  const current = layout.nodes[selectedNodeKey];
  const center = (op: OpLayout | AssetLayout): {x: number; y: number} => ({
    x: op.bounds.x + op.bounds.width / 2,
    y: op.bounds.y + op.bounds.height / 2,
  });

  /* Sort all the ops in the graph based on their attractiveness
    as a jump target. We want the nearest node in the exact same row for left/right,
    and the visually "closest" node above/below for up/down. */
  const score = (op: OpLayout | AssetLayout): number => {
    const dx = center(op).x - center(current).x;
    const dy = center(op).y - center(current).y;

    if (dir === 'left' && dy === 0 && dx < 0) {
      return -dx;
    }
    if (dir === 'right' && dy === 0 && dx > 0) {
      return dx;
    }
    if (dir === 'up' && dy < 0) {
      return -dy + Math.abs(dx) / 5;
    }
    if (dir === 'down' && dy > 0) {
      return dy + Math.abs(dx) / 5;
    }
    return Number.NaN;
  };

  const closest = Object.keys(layout.nodes)
    .map((name) => ({name, score: score(layout.nodes[name])}))
    .filter((e) => e.name !== selectedNodeKey && !Number.isNaN(e.score))
    .sort((a, b) => b.score - a.score)
    .pop();

  return closest ? closest.name : undefined;
};

/**
 * Identifies groups of ops that share a similar `prefix.` and returns
 * an array of bounding boxes and common prefixes. Used to render lightweight
 * outlines around flattened composites.
 */
export function computeNodeKeyPrefixBoundingBoxes(layout: OpGraphLayout) {
  const groups: {[base: string]: IBounds[]} = {};
  let maxDepth = 0;

  for (const key of Object.keys(layout.nodes)) {
    const parts = key.split('.');
    if (parts.length === 1) {
      continue;
    }
    for (let ii = 1; ii < parts.length; ii++) {
      const base = parts.slice(0, ii).join('.');
      groups[base] = groups[base] || [];
      groups[base].push(layout.nodes[key].bounds);
      maxDepth = Math.max(maxDepth, ii);
    }
  }

  const boxes: (IBounds & {name: string})[] = [];
  for (const base of Object.keys(groups)) {
    const group = groups[base];
    const depth = base.split('.').length;
    const margin = 5 + (maxDepth - depth) * 5;

    if (group.length === 1) {
      continue;
    }
    const x1 = Math.min(...group.map((l) => l.x)) - margin;
    const x2 = Math.max(...group.map((l) => l.x + l.width)) + margin;
    const y1 = Math.min(...group.map((l) => l.y)) - margin;
    const y2 = Math.max(...group.map((l) => l.y + l.height)) + margin;
    boxes.push({name: base, x: x1, y: y1, width: x2 - x1, height: y2 - y1});
  }

  return boxes;
}

export const position = ({x, y, width, height}: IBounds) => ({
  left: x,
  top: y,
  width,
  height,
  position: 'absolute' as const,
});
