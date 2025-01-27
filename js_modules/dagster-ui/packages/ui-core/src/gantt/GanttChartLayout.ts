import {Colors} from '@dagster-io/ui-components';

import {
  BOX_DOT_WIDTH_CUTOFF,
  BOX_SPACING_X,
  BOX_WIDTH,
  FLAT_INSET_FROM_PARENT,
  GanttChartBox,
  GanttChartLayout,
  GanttChartLayoutOptions,
  GanttChartMarker,
  GanttChartMode,
  IGanttNode,
  LEFT_INSET,
} from './Constants';
import {dynamicKeyWithoutIndex, isDynamicStep, isPlannedDynamicStep} from './DynamicStepSupport';
import {IRunMetadataDict, IStepAttempt, IStepState} from '../runs/RunMetadataProvider';

export interface BuildLayoutParams {
  nodes: IGanttNode[];
  mode: GanttChartMode;
}

export const buildLayout = (params: BuildLayoutParams) => {
  const {nodes, mode} = params;

  // Step 1: Place the nodes that have no dependencies into the layout.
  const hasNoDependencies = (g: IGanttNode) =>
    !g.inputs.some((i) => i.dependsOn.some((s) => nodes.find((o) => o.name === s.solid.name)));

  const boxes: GanttChartBox[] = nodes.filter(hasNoDependencies).map((node) => ({
    node,
    key: node.name,
    state: undefined,
    children: [],
    x: -1,
    y: -1,
    root: true,
    width: BOX_WIDTH,
  }));

  // Step 2: Recursively iterate through the graph and insert child nodes
  // into the `boxes` array, ensuring that their positions in the array are
  // always greater than their parent(s) position (which requires correction
  // because boxes can have multiple dependencies.)
  const roots = [...boxes];
  roots.forEach((box) => addChildren(boxes, box, params));

  // Step 3: Assign X values (pixels) to each box by traversing the graph from the
  // roots onward and pushing things to the right as we go.
  const deepen = (box: GanttChartBox, x: number) => {
    if (box.x >= x) {
      // If this box is already further to the right than required by it's parent,
      // we can safely stop traversing this branch of the graph.
      return;
    }
    box.x = x;
    box.children.forEach((child) => {
      if (child.key !== box.key) {
        deepen(child, box.x + box.width + BOX_SPACING_X);
      }
    });
  };
  roots.forEach((box) => deepen(box, LEFT_INSET));

  const parents: {[name: string]: GanttChartBox[]} = {};
  const boxesByY: {[y: string]: GanttChartBox[]} = {};

  // Step 4: Assign Y values (row numbers not pixel values)
  // First put each box on it's own line. We know this will generate a fine gantt viz
  // because we sorted the boxes array as we built it.
  boxes.forEach((box, idx) => {
    box.y = idx;
    box.children.forEach((child) => {
      const target = parents[child.node.name] || [];
      target.push(box);
      parents[child.node.name] = target;
    });
  });

  boxes.forEach((box) => {
    const target = boxesByY[`${box.y}`] || [];
    target.push(box);
    boxesByY[`${box.y}`] = target;
  });

  // Next, start at the bottom of the viz and "collapse" boxes up on to the previous line
  // as long as that does not result in them being higher than their parents AND does
  // not cause them to sit on top of an existing on-the-same-line A ---> B arrow.

  // This makes basic box series (A -> B -> C -> D) one row instead of four rows.

  let changed = true;
  while (changed) {
    changed = false;
    const boxesReversed = [...boxes].reverse();
    for (const box of boxesReversed) {
      const boxParents = parents[box.node.name] || [];
      const highestYParent = boxParents.sort((a, b) => b.y - a.y)[0];
      if (!highestYParent) {
        continue;
      }
      // Don't re-order the first row of nodes that "fan out" from a dynamic output. this
      // ensures that these nodes are always "waterfall" visually by ascending index.
      if (isDynamicStep(box.node.name) && !isDynamicStep(highestYParent.node.name)) {
        continue;
      }
      const onTargetY = boxesByY[`${highestYParent.y}`]!;
      const taken = onTargetY.find((r) => r.x === box.x);
      if (taken) {
        continue;
      }

      const parentX = highestYParent.x;
      const willCross = onTargetY.some((r) => r.x > parentX && r.x < box.x);
      const willCauseCrossing = onTargetY.some(
        (r) => r.x < box.x && r.children.some((c) => c.y >= highestYParent.y && c.x > box.x),
      );
      if (willCross || willCauseCrossing) {
        continue;
      }

      boxesByY[`${box.y}`] = boxesByY[`${box.y}`]!.filter((b) => b !== box);
      box.y = highestYParent.y;
      boxesByY[`${box.y}`]!.push(box);

      changed = true;
      break;
    }
  }

  if (mode === GanttChartMode.FLAT) {
    // Now that we've inlined chains of boxes where possible, flatten everything back out onto the
    // Y axis. Doing this after inlining ensures that children are close to their parents in the
    // resulting tree rather than placed randomly before their mutual dependents.
    let bottomY = 0;
    for (const y of Object.keys(boxesByY)) {
      const row = boxesByY[y]!;
      if (!row.length) {
        continue;
      }
      let x = row[0]!.root
        ? LEFT_INSET
        : parents[row[0]!.node.name]![0]!.x + FLAT_INSET_FROM_PARENT;
      for (const box of row) {
        box.x = x;
        box.y = bottomY;
        bottomY += 1;
        x += FLAT_INSET_FROM_PARENT;
      }
    }
    boxes.sort((a, b) => a.y - b.y || a.x - b.x);
  } else {
    // Since we've inlined boxes, shift rows up and fill empty space until every Y value has a box.
    changed = true;
    while (changed) {
      changed = false;
      const maxY = boxes.reduce((m, r) => Math.max(m, r.y), 0);
      for (let y = 0; y < maxY; y++) {
        const empty = !boxes.some((r) => r.y === y);
        if (empty) {
          boxes.filter((r) => r.y > y).forEach((r) => (r.y -= 1));
          changed = true;
          break;
        }
      }
    }
  }

  return {boxes, markers: []} as GanttChartLayout;
};

const ensureSubtreeAfterParentInArray = (
  boxes: GanttChartBox[],
  parent: GanttChartBox,
  box: GanttChartBox,
) => {
  const parentIdx = boxes.indexOf(parent);
  const boxIdx = boxes.indexOf(box);
  if (parentIdx <= boxIdx) {
    return;
  }
  boxes.splice(boxIdx, 1);
  boxes.splice(parentIdx, 0, box);

  // Note: It's important that we don't cache or pass indexes during this recursion.
  // Visiting a child below could cause boxes earlier in the array to be pulled to the
  // end. Our `parentIdx` above is not stable within the box.children loop below.

  for (const child of box.children) {
    ensureSubtreeAfterParentInArray(boxes, box, child);
  }
};

const addChildren = (boxes: GanttChartBox[], box: GanttChartBox, params: BuildLayoutParams) => {
  const seen: string[] = [];
  const seenSet: Set<string> = new Set();
  const added: GanttChartBox[] = [];

  for (const out of box.node.outputs) {
    for (const dep of out.dependedBy) {
      const depNode = params.nodes.find((n) => dep.solid.name === n.name);
      if (!depNode) {
        continue;
      }

      if (seenSet.has(depNode.name)) {
        continue;
      }

      // Hide the unresolved node if any its resolved node exists
      if (
        isPlannedDynamicStep(depNode.name) &&
        seen
          .filter((n) => isDynamicStep(n))
          .some((n) => dynamicKeyWithoutIndex(n) === dynamicKeyWithoutIndex(depNode.name))
      ) {
        continue;
      }

      seen.push(depNode.name);
      seenSet.add(depNode.name);

      const depBoxIdx = boxes.findIndex((r) => r.node === depNode);
      let depBox: GanttChartBox;

      if (depBoxIdx === -1) {
        depBox = {
          children: [],
          key: depNode.name,
          node: depNode,
          state: undefined,
          width: BOX_WIDTH,
          root: false,
          x: 0,
          y: -1,
        };
        boxes.push(depBox);
        added.push(depBox);
      } else {
        depBox = boxes[depBoxIdx]!;
        ensureSubtreeAfterParentInArray(boxes, box, depBox);
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

const TextColorForStates = {
  [IStepState.RUNNING]: Colors.textBlue(),
  [IStepState.RETRY_REQUESTED]: Colors.accentWhite(),
  [IStepState.SUCCEEDED]: Colors.accentWhite(),
  [IStepState.FAILED]: Colors.accentWhite(),
  [IStepState.SKIPPED]: Colors.accentWhite(),
  [IStepState.UNKNOWN]: Colors.accentWhite(),
};

const BackgroundColorForStates = {
  [IStepState.RUNNING]: Colors.backgroundBlue(),
  [IStepState.RETRY_REQUESTED]: Colors.accentYellow(),
  [IStepState.SUCCEEDED]: Colors.accentGreen(),
  [IStepState.FAILED]: Colors.accentRed(),
  [IStepState.SKIPPED]: Colors.accentGray(),
  [IStepState.UNKNOWN]: Colors.accentGrayHover(),
};

export const boxStyleFor = (
  state: IStepState | undefined,
  context: {
    metadata: IRunMetadataDict;
    options: {mode: GanttChartMode};
  },
) => {
  // Not running and not viewing waterfall? We always use a nice blue
  if (
    !context.metadata.startedPipelineAt &&
    context.options.mode !== GanttChartMode.WATERFALL_TIMED
  ) {
    return {background: `#2491eb`};
  }

  // Step has started and has state? Return state color.
  if (state && state !== IStepState.PREPARING) {
    return {
      color: TextColorForStates[state] || Colors.accentReversed(),
      background: BackgroundColorForStates[state] || Colors.backgroundLight(),
    };
  }

  // Step has not started, use "hypothetical dotted box".
  return {
    color: Colors.textLight(),
    background: Colors.backgroundDefault(),
    border: `1.5px dotted ${Colors.accentGray()}`,
  };
};

// Does a shallow clone of the boxes so attributes (`width`, `x`, etc) can be mutated.
// This requires special logic because (for easy graph travesal), boxes.children references
// other elements of the boxes array. A basic deepClone would replicate these into
// copies rather than references.
const cloneLayout = ({boxes, markers}: GanttChartLayout): GanttChartLayout => {
  const map = new WeakMap();
  const nextMarkers = markers.map((m) => ({...m}));
  const nextBoxes: GanttChartBox[] = [];
  for (const box of boxes) {
    const next = {...box};
    nextBoxes.push(next);
    map.set(box, next);
  }

  boxes.forEach((box, ii) => {
    nextBoxes[ii]!.children = box.children.map((c) => map.get(c));
  });

  return {boxes: nextBoxes, markers: nextMarkers};
};

const positionAndSplitBoxes = (
  boxes: GanttChartBox[],
  metadata: IRunMetadataDict,
  positionFor: (
    box: GanttChartBox,
    run?: IStepAttempt | null,
    runIdx?: number,
  ) => {width: number; x: number},
) => {
  // Apply X values + widths to boxes, and break apart retries into their own boxes by looking
  // at the transitions recorded for each step.
  for (let ii = boxes.length - 1; ii >= 0; ii--) {
    const box = boxes[ii]!;
    const meta = metadata.steps[box.node.name];
    if (!meta) {
      Object.assign(box, positionFor(box));
      continue;
    }
    if (meta.attempts.length === 0) {
      Object.assign(box, positionFor(box));
      box.state = meta.state;
      continue;
    }

    const runBoxes: GanttChartBox[] = [];
    meta.attempts.forEach((run, runIdx) => {
      runBoxes.push({
        ...box,
        ...positionFor(box, run, runIdx),
        key: `${box.key}-${runBoxes.length}`,
        state: run.exitState || IStepState.RUNNING,
      });
    });

    // Move the children (used to draw outbound lines) to the last box
    for (let jj = 0; jj < runBoxes.length - 1; jj++) {
      runBoxes[jj]!.children = [runBoxes[jj + 1]!];
    }
    runBoxes[runBoxes.length - 1]!.children = box.children;

    Object.assign(box, runBoxes[0]);
    // Add additional boxes we created for retries
    if (runBoxes.length > 1) {
      boxes.splice(ii, 0, ...runBoxes.slice(1));
    }
  }
};

/** Traverse the graph from the root and place boxes that still have x=0 locations.
(Unstarted or skipped boxes) so that they appear downstream of running boxes
we have position / time data for. */
const positionUntimedBoxes = (boxes: GanttChartBox[], beginUntimedBoxesAtX = 0) => {
  // If we have been provided a minimum X position for un-timed boxes (the "future" time
  // on the far right of the Gantt chart), we only need to visit untimed boxes because
  // their placement isn't based on their parents. If no "future" time is provided,
  // (waterfall mode) we visit the whole graph once, placing untimed boxes after their
  // timed ancestors.
  const queue = beginUntimedBoxesAtX ? boxes.filter((box) => box.x === 0) : [...boxes];

  const visit = (box: GanttChartBox, parentX: number) => {
    if (box.x === 0) {
      // If we are visiting the box for the first time and it's still in our queue,
      // remove that planned "visit". This happens if we reach this box by traversing
      // the tree from another starting box.
      const idx = queue.indexOf(box);
      if (idx !== -1) {
        queue.splice(idx, 1);
      }
    }

    box.x = Math.max(box.x, beginUntimedBoxesAtX || LEFT_INSET, parentX);

    const minXForUnstartedChildren = box.x + box.width + BOX_SPACING_X;
    for (const child of box.children) {
      if (child.x < minXForUnstartedChildren) {
        visit(child, minXForUnstartedChildren);
      }
    }
  };

  let box: GanttChartBox | undefined;
  while ((box = queue.shift())) {
    visit(box, beginUntimedBoxesAtX);
  }
};

export const adjustLayoutWithRunMetadata = (
  layout: GanttChartLayout,
  options: GanttChartLayoutOptions,
  metadata: IRunMetadataDict,
  scale: number,
  nowMs: number,
): GanttChartLayout => {
  // Clone the layout into a new set of JS objects so that React components can do shallow
  // comparison between the old set and the new set and code below can traverse + mutate
  // in place.
  let {boxes} = cloneLayout(layout);
  const markers: GanttChartMarker[] = [];

  // Move and size boxes based on the run metadata. Note that we don't totally invalidate
  // the pre-computed layout for the execution plan, (and shouldn't have to since the run's
  // step ordering, etc. should obey the constraints we already planned for). We just push
  // boxes around on their existing rows.
  if (options.mode === GanttChartMode.WATERFALL_TIMED) {
    const startedPipelineAt = metadata.startedPipelineAt || nowMs;
    const xForMs = (time: number) => LEFT_INSET + (time - startedPipelineAt) * scale;
    const widthForMs = ({start, end}: {start: number; end?: number}) =>
      Math.max(BOX_DOT_WIDTH_CUTOFF, ((end || nowMs) - start) * scale);

    positionAndSplitBoxes(boxes, metadata, (_box, attempt) => ({
      x: attempt ? xForMs(attempt.start) : 0,
      width: attempt ? widthForMs(attempt) : BOX_WIDTH,
    }));

    positionUntimedBoxes(boxes, xForMs(nowMs) + BOX_SPACING_X);

    // Add markers to the layout using the run metadata
    metadata.globalMarkers.forEach((m) => {
      if (m.start === undefined) {
        return;
      }
      markers.push({
        key: `global:${m.key}`,
        y: 0,
        x: xForMs(m.start),
        width: widthForMs({start: m.start, end: m.end}),
      });
    });
    Object.entries(metadata.steps).forEach(([name, step]) => {
      for (const m of step.markers) {
        if (m.start === undefined) {
          continue;
        }
        const stepBox = layout.boxes.find((b) => b.node.name === name);
        if (!stepBox) {
          continue;
        }

        markers.push({
          key: `${name}:${m.key}`,
          y: stepBox.y,
          x: xForMs(m.start),
          width: widthForMs({start: m.start, end: m.end}),
        });
      }
    });

    // Apply display options / filtering
    if (options.hideWaiting) {
      boxes = boxes.filter((b) => !!metadata.steps[b.node.name]?.state);
    }
  } else if (options.mode === GanttChartMode.WATERFALL) {
    positionAndSplitBoxes(boxes, metadata, (box, run, runIdx) => ({
      x: run ? box.x + (runIdx ? (BOX_SPACING_X + BOX_WIDTH) * runIdx : 0) : 0,
      width: BOX_WIDTH,
    }));
    positionUntimedBoxes(boxes);
  } else if (options.mode === GanttChartMode.FLAT) {
    positionAndSplitBoxes(boxes, metadata, (box, _run, runIdx) => ({
      x: box.x + (runIdx ? (2 + BOX_WIDTH) * runIdx : 0),
      width: BOX_WIDTH,
    }));
  } else {
    throw new Error('Invalid mdoe ');
  }

  return {boxes, markers};
};

/**
 * Returns a set of query presets that highlight interesting slices of the visualization.
 */
export const interestingQueriesFor = (metadata: IRunMetadataDict, layout: GanttChartLayout) => {
  if (layout.boxes.length === 0) {
    return;
  }
  const results: {name: string; value: string}[] = [];

  const errorsQuery = Object.keys(metadata.steps)
    .filter((k) => metadata.steps[k]!.state === IStepState.FAILED)
    .map((k) => `+${k}`)
    .join(', ');
  if (errorsQuery) {
    results.push({name: 'Errors', value: errorsQuery});
  }

  const slowStepsQuery = Object.keys(metadata.steps)
    .filter((k) => metadata.steps[k]?.end && metadata.steps[k]?.start)
    .sort(
      (a, b) =>
        metadata.steps[b]!.end! -
        metadata.steps[b]!.start! -
        (metadata.steps[a]!.end! - metadata.steps[a]!.start!),
    )
    .slice(0, 5)
    .map((k) => `"${k}"`)
    .join(', ');
  if (slowStepsQuery) {
    results.push({name: 'Slowest Individual Steps', value: slowStepsQuery});
  }

  const rightmostCompletedBox = [...layout.boxes]
    .filter((b) => metadata.steps[b.node.name]?.end)
    .sort((a, b) => b.x + b.width - (a.x + a.width))[0];

  if (rightmostCompletedBox) {
    results.push({
      name: 'Slowest Path',
      value: `*${rightmostCompletedBox.node.name}`,
    });
  }

  return results;
};
