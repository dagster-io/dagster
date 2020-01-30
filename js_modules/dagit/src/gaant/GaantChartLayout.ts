import { IRunMetadataDict } from "../RunMetadataProvider";
import { GraphQueryItem } from "../GraphQueryImpl";
import { Colors } from "@blueprintjs/core";
import {
  GaantChartLayoutOptions,
  GaantChartBox,
  BOX_SPACING_X,
  LEFT_INSET,
  GaantChartMode,
  GaantChartLayout,
  BOX_WIDTH,
  BOX_MIN_WIDTH,
  IGaantNode
} from "./Constants";

interface BuildLayoutParams {
  nodes: IGaantNode[];
  metadata: IRunMetadataDict;
  options: GaantChartLayoutOptions;
}

export const buildLayout = (params: BuildLayoutParams) => {
  const { nodes, metadata, options } = params;

  // Step 1: Place the nodes that have no dependencies into the layout.

  const hasNoDependencies = (g: IGaantNode) =>
    !g.inputs.some(i =>
      i.dependsOn.some(s => nodes.find(o => o.name === s.solid.name))
    );

  let boxes: GaantChartBox[] = nodes.filter(hasNoDependencies).map(node => ({
    node: node,
    children: [],
    x: -1,
    y: -1,
    width: boxWidthFor(node, params)
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
    box.x = Math.max(x, box.x);
    box.children.forEach(child =>
      deepen(child, box.x + box.width + BOX_SPACING_X)
    );
  };
  roots.forEach(box => deepen(box, LEFT_INSET));

  // Step 3.5: Assign X values based on the actual computation start times if we have them

  if (
    options.mode === GaantChartMode.WATERFALL_TIMED &&
    metadata.minStepStart
  ) {
    const deepenOrUseMetadata = (box: GaantChartBox, x: number) => {
      const start = metadata.steps[box.node.name]?.start;
      if (!start) {
        box.x = Math.max(x, box.x);
      } else {
        box.x = LEFT_INSET + (start - metadata.minStepStart!) * options.scale;
      }
      box.children.forEach(child =>
        deepenOrUseMetadata(child, box.x + box.width + BOX_SPACING_X)
      );
    };
    roots.forEach(box => deepenOrUseMetadata(box, LEFT_INSET));
  }

  // Step 4: Assign Y values (row numbers not pixel values)
  if (options.mode === GaantChartMode.FLAT) {
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

  // Apply display options / filtering
  if (options.mode === GaantChartMode.WATERFALL_TIMED && options.hideWaiting) {
    boxes = boxes.filter(b => {
      const state = metadata.steps[b.node.name]?.state || "waiting";
      return state !== "waiting";
    });
  }

  return { boxes } as GaantChartLayout;
};

const ensureSubtreeBelow = (
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
    ensureSubtreeBelow(boxes, boxes.indexOf(subchild), newIdx);
  }
};

const addChildren = (
  boxes: GaantChartBox[],
  box: GaantChartBox,
  params: BuildLayoutParams
) => {
  const idx = boxes.indexOf(box);
  const seen: string[] = [];

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
          width: boxWidthFor(depNode, params),
          x: 0,
          y: -1
        };
        boxes.push(depBox);
        addChildren(boxes, depBox, params);
      } else {
        depBox = boxes[depBoxIdx];
        ensureSubtreeBelow(boxes, depBoxIdx, idx);
      }

      box.children.push(depBox);
    }
  }
};

const boxWidthFor = (
  step: GraphQueryItem,
  context: { metadata: IRunMetadataDict; options: GaantChartLayoutOptions }
) => {
  const stepInfo = context.metadata.steps[step.name] || {};
  if (context.options.mode === GaantChartMode.WATERFALL_TIMED) {
    if (stepInfo.start) {
      return Math.max(
        BOX_MIN_WIDTH,
        ((stepInfo.finish || context.metadata.mostRecentLogAt) -
          stepInfo.start) *
          context.options.scale
      );
    }
  }
  return BOX_WIDTH;
};

const ColorsForStates = {
  running: Colors.GRAY3,
  succeeded: Colors.GREEN2,
  skipped: Colors.GOLD3,
  failed: Colors.RED3
};

export const boxStyleFor = (
  step: GraphQueryItem,
  context: { metadata: IRunMetadataDict; options: GaantChartLayoutOptions }
) => {
  let color = "#2491eb";

  if (context.options.mode === GaantChartMode.WATERFALL_TIMED) {
    const info = context.metadata.steps[step.name];
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

/**
 * Returns a set of query presets that highlight interesting slices of the visualization.
 */
export const interestingQueriesFor = (
  metadata: IRunMetadataDict,
  layout: GaantChartLayout
) => {
  if (layout.boxes.length === 0) return;

  const errorsQuery = Object.keys(metadata.steps)
    .filter(k => metadata.steps[k].state === "failed")
    .map(k => `+${k}`)
    .join(", ");

  const slowestStepsQuery = Object.keys(metadata.steps)
    .filter(k => metadata.steps[k]?.finish && metadata.steps[k]?.start)
    .sort(
      (a, b) =>
        metadata.steps[b]!.finish! -
        metadata.steps[b]!.start! -
        (metadata.steps[a]!.finish! - metadata.steps[a]!.start!)
    )
    .slice(0, 5)
    .map(k => `${k}`)
    .join(", ");

  const rightmostBox = [...layout.boxes].sort(
    (a, b) => b.x + b.width - (a.x + a.width)
  )[0];
  const slowestPathQuery = `*${rightmostBox.node.name}`;

  return [
    { name: "Errors", value: errorsQuery },
    { name: "Slowest Individual Steps", value: slowestStepsQuery },
    { name: "Slowest Path", value: slowestPathQuery }
  ];
};
