import type {IBounds} from '../graph/common';
import {assertExists} from '../util/invariant';

export type CompactLayoutOptions = {
  /**
   * The axis boxes move along: `y` for left-to-right layouts, `x` for top-to-bottom ones.
   * Positions on the other axis never change. Defaults to `y`.
   */
  axis?: 'x' | 'y';
  /**
   * Packing closes gaps wider than this down to it. 0 packs as tightly as possible.
   * Relaxation can reopen wider gaps to line boxes up, without growing the overall extent.
   */
  maxGap: number;
  /** Minimum spacing between two leaf boxes. */
  nodeGap: number;
  /** Minimum spacing when either box is an expanded group. */
  groupGap: number;
  /** Padding added around an expanded group's children, matching how group boxes are drawn. */
  groupPadding: {x: number; top: number; bottom: number};
  /** Pull boxes toward the position of their neighbors after packing. */
  relax?: boolean;
  /**
   * When relaxing, each box moves to minimize the total offset of its edges, minus this
   * bonus (in px) for every edge it makes perfectly straight. 0 moves to the median offset.
   */
  straightEdgeBonus?: number;
};

export type CompactLayoutInput = {
  /** Leaf boxes (assets, links, collapsed groups). Updated in place along `axis`. */
  boxes: {[id: string]: IBounds};
  /** Expanded group ids. */
  groups: string[];
  /** The expanded group directly containing a leaf box or group, or undefined at the top level. */
  parentOf: (id: string) => string | undefined;
  edges: {v: string; w: string}[];
};

type Item = IBounds & {leaves: string[]; isGroup: boolean};

/** Group padding before and after the children, across and along the packing axis. */
type Padding = {crossBefore: number; crossAfter: number; before: number; after: number};

const ROOT = '';
const RELAX_ITERATIONS = 30;

/**
 * Removes excess space across the ranks of a layered layout. Positions along the rank direction
 * never change, so edges that pointed forward still do. Expanded groups move as rigid boxes and
 * are packed innermost-first. Boxes keep their order, so nothing overlaps.
 */
export function compactLayout(input: CompactLayoutInput, opts: CompactLayoutOptions) {
  const {x, top, bottom} = opts.groupPadding;
  if (opts.axis !== 'x') {
    compactAlongY(input, opts, {crossBefore: x, crossAfter: x, before: top, after: bottom});
    return;
  }
  // Swap the axes, compact along y, and copy the results back to x.
  const transpose = (b: IBounds): IBounds => ({x: b.y, y: b.x, width: b.height, height: b.width});
  const flipped = Object.fromEntries(
    Object.entries(input.boxes).map(([id, b]) => [id, transpose(b)]),
  );
  compactAlongY({...input, boxes: flipped}, opts, {
    crossBefore: top,
    crossAfter: bottom,
    before: x,
    after: x,
  });
  for (const [id, b] of Object.entries(flipped)) {
    const target = input.boxes[id];
    if (target) {
      target.x = b.y;
    }
  }
}

function compactAlongY(input: CompactLayoutInput, opts: CompactLayoutOptions, pad: Padding) {
  const {boxes} = input;
  const boxAt = (id: string) => assertExists(boxes[id]);
  const groupSet = new Set(input.groups);
  const containerOf = (id: string) => {
    const parent = input.parentOf(id);
    return parent !== undefined && groupSet.has(parent) ? parent : ROOT;
  };

  const children = new Map<string, {leaves: string[]; groups: string[]}>();
  const childrenOf = (id: string) => {
    let c = children.get(id);
    if (!c) {
      c = {leaves: [], groups: []};
      children.set(id, c);
    }
    return c;
  };
  for (const id of Object.keys(boxes)) {
    childrenOf(containerOf(id)).leaves.push(id);
  }
  for (const id of input.groups) {
    childrenOf(containerOf(id)).groups.push(id);
  }

  const leavesUnder = new Map<string, string[]>();
  const collectLeaves = (id: string): string[] => {
    let out = leavesUnder.get(id);
    if (!out) {
      const c = childrenOf(id);
      out = [...c.leaves, ...c.groups.flatMap(collectLeaves)];
      leavesUnder.set(id, out);
    }
    return out;
  };

  const depthOf = (id: string): number => {
    const parent = containerOf(id);
    return parent === ROOT ? 0 : depthOf(parent) + 1;
  };
  const innermostFirst = input.groups
    .filter((id) => collectLeaves(id).length > 0)
    .sort((a, b) => depthOf(b) - depthOf(a));

  const groupBounds = (id: string): IBounds => {
    const c = childrenOf(id);
    const parts = [
      ...c.leaves.map(boxAt),
      ...c.groups.filter((g) => collectLeaves(g).length > 0).map(groupBounds),
    ];
    const x0 = Math.min(...parts.map((b) => b.x));
    const y0 = Math.min(...parts.map((b) => b.y));
    const x1 = Math.max(...parts.map((b) => b.x + b.width));
    const y1 = Math.max(...parts.map((b) => b.y + b.height));
    return {
      x: x0 - pad.crossBefore,
      y: y0 - pad.before,
      width: x1 - x0 + pad.crossBefore + pad.crossAfter,
      height: y1 - y0 + pad.before + pad.after,
    };
  };

  const itemsIn = (container: string): Item[] => {
    const c = childrenOf(container);
    return [
      ...c.leaves.map((id) => ({...boxAt(id), leaves: [id], isGroup: false})),
      ...c.groups
        .filter((id) => collectLeaves(id).length > 0)
        .map((id) => ({...groupBounds(id), leaves: collectLeaves(id), isGroup: true})),
    ];
  };

  const shift = (item: Item, dy: number) => {
    item.y += dy;
    for (const id of item.leaves) {
      boxAt(id).y += dy;
    }
  };

  const gap = (a: Item, b: Item) => (a.isGroup || b.isGroup ? opts.groupGap : opts.nodeGap);

  const neighbors = new Map<string, string[]>();
  const addNeighbor = (a: string, b: string) => {
    const list = neighbors.get(a);
    if (list) {
      list.push(b);
    } else {
      neighbors.set(a, [b]);
    }
  };
  for (const {v, w} of input.edges) {
    if (boxes[v] && boxes[w]) {
      addNeighbor(v, w);
      addNeighbor(w, v);
    }
  }
  const centerY = (id: string) => {
    const b = boxAt(id);
    return b.y + b.height / 2;
  };

  const containers = [...innermostFirst, ROOT];
  for (const container of containers) {
    pack(itemsIn(container), gap, shift, opts.maxGap);
  }
  if (opts.relax !== false) {
    for (const container of containers) {
      const items = itemsIn(container);
      // Each relaxation stays within the container's current extent, so containers don't grow.
      const deltas = (item: Item) => {
        const own = new Set(item.leaves);
        const out: number[] = [];
        for (const id of item.leaves) {
          for (const other of neighbors.get(id) || []) {
            if (!own.has(other)) {
              out.push(centerY(other) - centerY(id));
            }
          }
        }
        return out;
      };
      relax(items, gap, shift, deltas, opts.straightEdgeBonus ?? 0);
    }
  }
}

const xOverlap = (a: IBounds, b: IBounds) => a.x < b.x + b.width - 1 && b.x < a.x + a.width - 1;

/**
 * For each item, the nearest item above it in each column (distinct x-range) it overlaps.
 * Items in a column keep their order, so only the nearest one can constrain the item.
 */
function nearestAbove(items: Item[]) {
  const order = items
    .map((_, i) => i)
    .sort(
      (a, b) => itemAt(items, a).y - itemAt(items, b).y || itemAt(items, a).x - itemAt(items, b).x,
    );
  const lastInColumn = new Map<string, number>();
  const above = items.map((): number[] => []);
  for (const i of order) {
    const item = itemAt(items, i);
    for (const j of lastInColumn.values()) {
      if (xOverlap(itemAt(items, j), item)) {
        above[i]?.push(j);
      }
    }
    lastInColumn.set(`${item.x}:${item.width}`, i);
  }
  return {order, above};
}

const itemAt = (items: Item[], i: number) => assertExists(items[i]);

/** Moves each item up, in vertical order, until it sits `maxGap` below the items above it. */
function pack(
  items: Item[],
  gap: (a: Item, b: Item) => number,
  shift: (item: Item, dy: number) => void,
  maxGap: number,
) {
  if (!items.length) {
    return;
  }
  const top = Math.min(...items.map((i) => i.y));
  const {order, above} = nearestAbove(items);
  for (const i of order) {
    const item = itemAt(items, i);
    let floor = top;
    for (const j of above[i] || []) {
      const other = itemAt(items, j);
      floor = Math.max(floor, other.y + other.height + gap(other, item));
    }
    shift(item, Math.max(floor, Math.min(item.y, floor + maxGap)) - item.y);
  }
}

/**
 * Pulls each item toward its neighbors, clamped between the items directly above and below it.
 * Never reorders items or grows the overall extent.
 */
function relax(
  items: Item[],
  gap: (a: Item, b: Item) => number,
  shift: (item: Item, dy: number) => void,
  deltas: (item: Item) => number[],
  straightEdgeBonus: number,
) {
  if (!items.length) {
    return;
  }
  const top = Math.min(...items.map((i) => i.y));
  const bottom = Math.max(...items.map((i) => i.y + i.height));
  const {above} = nearestAbove(items);
  const below = items.map((): number[] => []);
  above.forEach((uppers, lower) => {
    for (const upper of uppers) {
      below[upper]?.push(lower);
    }
  });

  for (let iteration = 0; iteration < RELAX_ITERATIONS; iteration++) {
    const order = items.map((_, i) => i).sort((a, b) => itemAt(items, a).y - itemAt(items, b).y);
    if (iteration % 2) {
      order.reverse();
    }
    let moved = false;
    for (const i of order) {
      const item = itemAt(items, i);
      const d = deltas(item).sort((a, b) => a - b);
      let lo = top - item.y;
      let hi = bottom - (item.y + item.height);
      for (const u of above[i] || []) {
        const other = itemAt(items, u);
        lo = Math.max(lo, other.y + other.height + gap(other, item) - item.y);
      }
      for (const l of below[i] || []) {
        const other = itemAt(items, l);
        hi = Math.min(hi, other.y - gap(item, other) - (item.y + item.height));
      }
      if (lo > hi) {
        continue;
      }
      // A box with no edges to line up with moves up as far as it can.
      const want = d.length ? Math.round(bestShift(d, lo, hi, straightEdgeBonus)) : lo;
      const dy = Math.max(lo, Math.min(hi, want));
      if (Math.abs(dy) >= 1) {
        shift(item, dy);
        moved = true;
      }
    }
    if (!moved) {
      break;
    }
  }
}

/** The shift within [lo, hi] that minimizes total edge offset, less a bonus per straight edge. */
function bestShift(sortedDeltas: number[], lo: number, hi: number, straightEdgeBonus: number) {
  const clamp = (v: number) => Math.max(lo, Math.min(hi, v));
  const median = clamp(assertExists(sortedDeltas[Math.floor(sortedDeltas.length / 2)]));
  if (!straightEdgeBonus) {
    return median;
  }
  const cost = (dy: number) => {
    let total = 0;
    for (const d of sortedDeltas) {
      const offset = Math.abs(d - dy);
      total += offset < 1 ? -straightEdgeBonus : offset;
    }
    return total;
  };
  let best = median;
  let bestCost = cost(median);
  for (const d of sortedDeltas) {
    const candidate = clamp(d);
    const c = cost(candidate);
    if (c < bestCost) {
      best = candidate;
      bestCost = c;
    }
  }
  return best;
}
