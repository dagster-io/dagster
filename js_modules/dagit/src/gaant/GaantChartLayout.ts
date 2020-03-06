import { IRunMetadataDict, IStepState } from "../RunMetadataProvider";
import { Colors } from "@blueprintjs/core";
import {
  GaantChartLayoutOptions,
  GaantChartBox,
  BOX_SPACING_X,
  LEFT_INSET,
  GaantChartMode,
  GaantChartLayout,
  BOX_WIDTH,
  BOX_DOT_WIDTH_CUTOFF,
  IGaantNode,
  GaantChartMarker
} from "./Constants";

export interface BuildLayoutParams {
  nodes: IGaantNode[];
  mode: GaantChartMode;
}

export const buildLayout = (params: BuildLayoutParams) => {
  const { nodes, mode } = params;

  // Step 1: Place the nodes that have no dependencies into the layout.

  const hasNoDependencies = (g: IGaantNode) =>
    !g.inputs.some(i =>
      i.dependsOn.some(s => nodes.find(o => o.name === s.solid.name))
    );

  const boxes: GaantChartBox[] = nodes.filter(hasNoDependencies).map(node => ({
    node: node,
    children: [],
    x: -1,
    y: -1,
    root: true,
    width: BOX_WIDTH
  }));

  // Step 2: Recursively iterate through the graph and insert child nodes
  // into the `boxes` array, ensuring that their positions in the array are
  // always greater than their parent(s) position (which requires correction
  // because boxes can have multiple dependencies.)
  const roots = [...boxes];
  roots.forEach(box => addChildren(boxes, box, params));

  // Step 3: Assign X values (pixels) to each box by traversing the graph from the
  // roots onward and pushing things to the right as we go.
  const deepen = (box: GaantChartBox, x: number) => {
    if (box.x >= x) {
      // If this box is already further to the right than required by it's parent,
      // we can safely stop traversing this branch of the graph.
      return;
    }
    box.x = x;
    box.children.forEach(child =>
      deepen(child, box.x + box.width + BOX_SPACING_X)
    );
  };
  roots.forEach(box => deepen(box, LEFT_INSET));

  // Step 4: Assign Y values (row numbers not pixel values)
  if (mode === GaantChartMode.FLAT) {
    boxes.forEach((box, idx) => {
      box.y = idx;
      box.width = 400;
      box.x = LEFT_INSET + box.x * 0.1;
    });
  } else {
    const parents: { [name: string]: GaantChartBox[] } = {};
    const boxesByY: { [y: string]: GaantChartBox[] } = {};

    // First put each box on it's own line. We know this will generate a fine gaant viz
    // because we sorted the boxes array as we built it.
    boxes.forEach((box, idx) => {
      box.y = idx;
      box.children.forEach(child => {
        parents[child.node.name] = parents[child.node.name] || [];
        parents[child.node.name].push(box);
      });
    });

    boxes.forEach(box => {
      boxesByY[`${box.y}`] = boxesByY[`${box.y}`] || [];
      boxesByY[`${box.y}`].push(box);
    });

    // Next, start at the bottom of the viz and "collapse" boxes up on to the previous line
    // as long as that does not result in them being higher than their parents AND does
    // not cause them to sit on top of an existing on-the-same-line A ---> B arrow.

    // This makes basic box series (A -> B -> C -> D) one row instead of four rows.

    let changed = true;
    while (changed) {
      changed = false;
      for (let idx = boxes.length - 1; idx > 0; idx--) {
        const box = boxes[idx];
        const boxParents = parents[box.node.name] || [];
        const highestYParent = boxParents.sort((a, b) => b.y - a.y)[0];
        if (!highestYParent) continue;

        const onTargetY = boxesByY[`${highestYParent.y}`];
        const taken = onTargetY.find(r => r.x === box.x);
        if (taken) continue;

        const parentX = highestYParent.x;
        const willCross = onTargetY.some(r => r.x > parentX && r.x < box.x);
        const willCauseCrossing = onTargetY.some(
          r =>
            r.x < box.x &&
            r.children.some(c => c.y >= highestYParent.y && c.x > box.x)
        );
        if (willCross || willCauseCrossing) continue;

        boxesByY[`${box.y}`] = boxesByY[`${box.y}`].filter(b => b !== box);
        box.y = highestYParent.y;
        boxesByY[`${box.y}`].push(box);

        changed = true;
        break;
      }
    }

    // The collapsing above can leave rows entirely empty - shift rows up and fill empty
    // space until every Y value has a box.
    changed = true;
    while (changed) {
      changed = false;
      const maxY = boxes.reduce((m, r) => Math.max(m, r.y), 0);
      for (let y = 0; y < maxY; y++) {
        const empty = !boxes.some(r => r.y === y);
        if (empty) {
          boxes.filter(r => r.y > y).forEach(r => (r.y -= 1));
          changed = true;
          break;
        }
      }
    }
  }

  return { boxes, markers: [] } as GaantChartLayout;
};

const ensureChildrenAfterParentInArray = (
  boxes: GaantChartBox[],
  childIdx: number,
  parentIdx: number
) => {
  if (parentIdx <= childIdx) {
    return;
  }
  const [child] = boxes.splice(childIdx, 1);
  boxes.push(child);
  const newIdx = boxes.length - 1;
  for (const subchild of child.children) {
    ensureChildrenAfterParentInArray(boxes, boxes.indexOf(subchild), newIdx);
  }
};

const addChildren = (
  boxes: GaantChartBox[],
  box: GaantChartBox,
  params: BuildLayoutParams
) => {
  const idx = boxes.indexOf(box);
  const seen: string[] = [];
  const added: GaantChartBox[] = [];

  for (const out of box.node.outputs) {
    for (const dep of out.dependedBy) {
      const depNode = params.nodes.find(n => dep.solid.name === n.name);
      if (!depNode) continue;

      if (seen.includes(depNode.name)) continue;
      seen.push(depNode.name);

      const depBoxIdx = boxes.findIndex(r => r.node === depNode);
      let depBox: GaantChartBox;

      if (depBoxIdx === -1) {
        depBox = {
          children: [],
          node: depNode,
          width: BOX_WIDTH,
          root: false,
          x: 0,
          y: -1
        };
        boxes.push(depBox);
        added.push(depBox);
      } else {
        depBox = boxes[depBoxIdx];
        ensureChildrenAfterParentInArray(boxes, depBoxIdx, idx);
      }

      box.children.push(depBox);
    }
  }

  // Note: To limit the amount of time we spend shifting elements of our `boxes` array to keep it
  // ordered (knowing that parents appear before children gives us more opportunities for early
  // returns, etc. elsewhere), we add all of our immediate children and THEN proceed in to the next layer.
  for (const depBox of added) {
    addChildren(boxes, depBox, params);
  }
};

const boxWidthFor = (
  { start, end }: { start?: number; end?: number },
  options: GaantChartLayoutOptions,
  scale: number,
  nowMs: number
) => {
  if (options.mode === GaantChartMode.WATERFALL_TIMED && start) {
    return Math.max(BOX_DOT_WIDTH_CUTOFF, ((end || nowMs) - start) * scale);
  }
  return BOX_WIDTH;
};

const ColorsForStates = {
  [IStepState.RUNNING]: Colors.GRAY3,
  [IStepState.SUCCEEDED]: Colors.GREEN2,
  [IStepState.SKIPPED]: Colors.GOLD3,
  [IStepState.FAILED]: Colors.RED3
};

export const boxStyleFor = (
  stepName: string,
  context: {
    metadata: IRunMetadataDict;
    options: { mode: GaantChartMode };
  }
) => {
  let color = "#2491eb";

  if (
    context.metadata.firstLogAt ||
    context.options.mode === GaantChartMode.WATERFALL_TIMED
  ) {
    const info = context.metadata.steps[stepName];
    if (!info || info.state === "waiting") {
      return {
        color: Colors.DARK_GRAY4,
        background: Colors.WHITE,
        border: `1.5px dotted ${Colors.LIGHT_GRAY1}`,
        boxShadow: `none`
      };
    }
    color = ColorsForStates[info.state] || Colors.GRAY3;
  }

  return {
    background: `${color} linear-gradient(180deg, rgba(255,255,255,0.15), rgba(0,0,0,0.1))`
  };
};

// Does a shallow clone of the boxes so attributes (`width`, `x`, etc) can be mutated.
// This requires special logic because (for easy graph travesal), boxes.children references
// other elements of the boxes array. A basic deepClone would replicate these into
// copies rather than references.
const cloneLayout = ({
  boxes,
  markers
}: GaantChartLayout): GaantChartLayout => {
  const map = new WeakMap();
  const nextMarkers = markers.map(m => ({ ...m }));
  const nextBoxes: GaantChartBox[] = [];
  for (const box of boxes) {
    const next = { ...box };
    nextBoxes.push(next);
    map.set(box, next);
  }
  for (let ii = 0; ii < boxes.length; ii++) {
    nextBoxes[ii].children = boxes[ii].children.map(c => map.get(c));
  }

  return { boxes: nextBoxes, markers: nextMarkers };
};

export const adjustLayoutWithRunMetadata = (
  layout: GaantChartLayout,
  options: GaantChartLayoutOptions,
  metadata: IRunMetadataDict,
  scale: number,
  nowMs: number
): GaantChartLayout => {
  // Clone the layout into a new set of JS objects so that React components can do shallow
  // comparison between the old set and the new set and code below can traverse + mutate
  // in place.
  let { boxes } = cloneLayout(layout);
  const markers: GaantChartMarker[] = [];
  const { firstLogAt } = metadata;

  // Move and size boxes based on the run metadata. Note that we don't totally invalidate
  // the pre-computed layout for the execution plan, (and shouldn't have to since the run's
  // step ordering, etc. should obey the constraints we already planned for). We just push
  // boxes around on their existing rows.
  if (options.mode === GaantChartMode.WATERFALL_TIMED && firstLogAt) {
    const xForMs = (time: number) => LEFT_INSET + (time - firstLogAt!) * scale;

    // Apply all box widths
    for (const box of boxes) {
      box.width = boxWidthFor(
        metadata.steps[box.node.name] || {},
        options,
        scale,
        nowMs
      );
    }

    // Traverse the graph and push boxes right as we go to account for new widths
    const deepenOrUseMetadata = (box: GaantChartBox, parentX: number) => {
      const start = metadata.steps[box.node.name]?.start;

      box.x = start
        ? xForMs(start)
        : Math.max(parentX, box.x, xForMs(nowMs) + BOX_SPACING_X);

      const minXForUnstartedChildren = box.x + box.width + BOX_SPACING_X;
      for (const child of box.children) {
        deepenOrUseMetadata(child, minXForUnstartedChildren);
      }
    };

    boxes
      .filter(box => box.root)
      .forEach(box => deepenOrUseMetadata(box, LEFT_INSET));

    // Add markers to the layout using the run metadata
    metadata.globalMarkers.forEach(m => {
      if (m.start === undefined) return;
      markers.push({
        key: m.key,
        y: 0,
        x: xForMs(m.start),
        width: boxWidthFor(m, options, scale, nowMs)
      });
    });
    Object.entries(metadata.steps).forEach(([name, step]) => {
      for (const m of step.markers) {
        if (m.start === undefined) return;
        markers.push({
          key: `${name}:${m.key}`,
          y: layout.boxes.find(b => b.node.name === name)!.y,
          x: xForMs(m.start),
          width: boxWidthFor(m, options, scale, nowMs)
        });
      }
    });
  }

  // Apply display options / filtering
  if (options.mode === GaantChartMode.WATERFALL_TIMED && options.hideWaiting) {
    boxes = boxes.filter(b => {
      const state = metadata.steps[b.node.name]?.state || "waiting";
      return state !== "waiting";
    });
  }

  return { boxes, markers };
};

/**
 * Returns a set of query presets that highlight interesting slices of the visualization.
 */
export const interestingQueriesFor = (
  metadata: IRunMetadataDict,
  layout: GaantChartLayout
) => {
  if (layout.boxes.length === 0) {
    return;
  }
  const results: { name: string; value: string }[] = [];

  const errorsQuery = Object.keys(metadata.steps)
    .filter(k => metadata.steps[k].state === IStepState.FAILED)
    .map(k => `+${k}`)
    .join(", ");
  if (errorsQuery) {
    results.push({ name: "Errors", value: errorsQuery });
  }

  const slowStepsQuery = Object.keys(metadata.steps)
    .filter(k => metadata.steps[k]?.end && metadata.steps[k]?.start)
    .sort(
      (a, b) =>
        metadata.steps[b]!.end! -
        metadata.steps[b]!.start! -
        (metadata.steps[a]!.end! - metadata.steps[a]!.start!)
    )
    .slice(0, 5)
    .map(k => `${k}`)
    .join(", ");
  if (slowStepsQuery) {
    results.push({ name: "Slowest Individual Steps", value: slowStepsQuery });
  }

  const rightmostCompletedBox = [...layout.boxes]
    .filter(b => metadata.steps[b.node.name]?.end)
    .sort((a, b) => b.x + b.width - (a.x + a.width))[0];

  if (rightmostCompletedBox) {
    results.push({
      name: "Slowest Path",
      value: `*${rightmostCompletedBox.node.name}`
    });
  }

  return results;
};
