import * as React from "react";
import styled from "styled-components/macro";
import { weakmapMemoize } from "./Util";
import { IRunMetadataDict } from "./RunMetadataProvider";
import { GaantChartExecutionPlanFragment } from "./types/GaantChartExecutionPlanFragment";
import { RunFragment } from "./runs/types/RunFragment";
import { GraphQueryInput } from "./GraphQueryInput";
import { filterByQuery, GraphQueryItem } from "./GraphQueryImpl";
import {
  Slider,
  ButtonGroup,
  Button,
  Colors,
  Checkbox
} from "@blueprintjs/core";
import gql from "graphql-tag";

type IGaantNode = GraphQueryItem;

interface GaantChartProps {
  options?: Partial<GaantChartLayoutOptions>;
  plan: GaantChartExecutionPlanFragment;
  metadata?: IRunMetadataDict;
  toolbarActions?: React.ReactChild;
  toolbarLeftActions?: React.ReactChild;
  run?: RunFragment;

  onApplyStepFilter?: (step: string) => void;
}

interface GaantChartBox {
  children: GaantChartBox[];
  node: IGaantNode;
  x: number;
  width: number;
  y: number;
}

interface GaantChartLayout {
  boxes: GaantChartBox[];
}

interface GaantChartLayoutOptions {
  mode: GaantChartMode;
  scale: number;
  hideWaiting: boolean;
}

export enum GaantChartMode {
  FLAT = "flat",
  WATERFALL = "waterfall",
  WATERFALL_TIMED = "waterfall-timed"
}

const LEFT_INSET = 5;
const BOX_HEIGHT = 30;
const BOX_MARGIN_Y = 5;
const BOX_SPACING_X = 20;
const BOX_WIDTH = 100;
const BOX_MIN_WIDTH = 6;
const LINE_SIZE = 2;

/**
 * Converts a Run execution plan into a tree of `GraphQueryItem` items that
 * can be used as the input to the "solid query" filtering algorithm. The idea
 * is that this data structure is generic, but it's really a fake solid tree.
 */
const toGraphQueryItems = weakmapMemoize(
  (plan: GaantChartExecutionPlanFragment) => {
    const nodeTable: { [key: string]: IGaantNode } = {};

    for (const step of plan.steps) {
      const node: IGaantNode = {
        name: step.key,
        inputs: [],
        outputs: []
      };
      nodeTable[step.key] = node;
    }

    for (const step of plan.steps) {
      for (const input of step.inputs) {
        nodeTable[step.key].inputs.push({
          dependsOn: input.dependsOn.map(d => ({
            solid: {
              name: d.key
            }
          }))
        });

        for (const upstream of input.dependsOn) {
          let output = nodeTable[upstream.key].outputs[0];
          if (!output) {
            output = {
              dependedBy: []
            };
            nodeTable[upstream.key].outputs.push(output);
          }
          output.dependedBy.push({
            solid: { name: step.key }
          });
        }
      }
    }

    return Object.values(nodeTable);
  }
);

const boxWidthFor = (
  step: GraphQueryItem,
  { metadata, options }: BuildLayoutParams
) => {
  const stepInfo = metadata.steps[step.name] || {};
  if (options.mode === GaantChartMode.WATERFALL_TIMED) {
    const width =
      stepInfo.finish && stepInfo.start
        ? stepInfo.finish - stepInfo.start
        : stepInfo.start
        ? Date.now() - stepInfo.start
        : BOX_WIDTH;
    return Math.max(BOX_MIN_WIDTH, width * options.scale);
  }
  return BOX_WIDTH;
};

const boxColorFor = (step: GraphQueryItem, metadata: IRunMetadataDict) => {
  const stepInfo = metadata.steps[step.name] || {};
  return (
    {
      waiting: Colors.GRAY1,
      running: Colors.GRAY3,
      succeeded: Colors.GREEN2,
      skipped: Colors.GOLD3,
      failed: Colors.RED3
    }[stepInfo.state] || "#2491eb"
  );
};

/**
 * Returns a set of query presets that highlight interesting slices of the visualization.
 */
const interestingQueriesFor = (
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

// Layout Logic

interface BuildLayoutParams {
  nodes: IGaantNode[];
  metadata: IRunMetadataDict;
  options: GaantChartLayoutOptions;
}

const buildLayout = (params: BuildLayoutParams) => {
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

// React Component

interface GaantChartState {
  options: GaantChartLayoutOptions;
  query: string;
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  static fragments = {
    GaantChartExecutionPlanFragment: gql`
      fragment GaantChartExecutionPlanFragment on ExecutionPlan {
        steps {
          key
          kind
        }
        steps {
          key
          inputs {
            dependsOn {
              key
              outputs {
                name
                type {
                  name
                }
              }
            }
          }
        }
        artifactsPersisted
      }
    `
  };

  constructor(props: GaantChartProps) {
    super(props);

    this.state = {
      query: "*",
      options: Object.assign(
        {
          mode: GaantChartMode.WATERFALL,
          hideWaiting: true,
          scale: 0.8
        },
        props.options
      )
    };
  }

  render() {
    const { metadata = { steps: {} }, plan } = this.props;
    const { query, options } = this.state;

    const graph = toGraphQueryItems(plan);
    const graphFiltered = filterByQuery(graph, query);
    const layout = buildLayout({
      nodes: graphFiltered.all,
      metadata,
      options
    });

    // todo perf: We can break buildLayout into a function that does not need metadata
    // and then a post-processor that resizes/shifts things using `metadata`. Then we can
    // memoize the time consuming vertical layout work.

    const setOptions = (changes: Partial<GaantChartLayoutOptions>) => {
      this.setState({ ...this.state, options: { ...options, ...changes } });
    };

    return (
      <GaantChartContainer>
        <OptionsContainer>
          {this.props.toolbarLeftActions}
          {this.props.toolbarLeftActions && <OptionsDivider />}
          <ButtonGroup style={{ flexShrink: 0 }}>
            <Button
              key={GaantChartMode.FLAT}
              small={true}
              icon="column-layout"
              title={"Flat"}
              active={options.mode === GaantChartMode.FLAT}
              onClick={() => setOptions({ mode: GaantChartMode.FLAT })}
            />
            <Button
              key={GaantChartMode.WATERFALL}
              small={true}
              icon="gantt-chart"
              title={"Waterfall"}
              active={options.mode === GaantChartMode.WATERFALL}
              onClick={() => setOptions({ mode: GaantChartMode.WATERFALL })}
            />
            <Button
              key={GaantChartMode.WATERFALL_TIMED}
              small={true}
              icon="time"
              rightIcon="gantt-chart"
              title={"Waterfall with Execution Timing"}
              active={options.mode === GaantChartMode.WATERFALL_TIMED}
              onClick={() =>
                setOptions({ mode: GaantChartMode.WATERFALL_TIMED })
              }
            />
          </ButtonGroup>
          {options.mode === GaantChartMode.WATERFALL_TIMED && (
            <>
              <div style={{ width: 15 }} />
              <Checkbox
                style={{ marginBottom: 0 }}
                label="Hide waiting"
                checked={options.hideWaiting}
                onClick={() =>
                  setOptions({ hideWaiting: !options.hideWaiting })
                }
              />
              <div style={{ width: 15 }} />
              <div style={{ width: 200 }}>
                <Slider
                  min={0.01}
                  max={1}
                  stepSize={0.05}
                  labelRenderer={false}
                  value={options.scale}
                  onChange={v => setOptions({ scale: v })}
                />
              </div>
            </>
          )}
          <div style={{ flex: 1 }} />
          {this.props.toolbarActions}
        </OptionsContainer>
        <GaantChartContent {...this.props} {...this.state} layout={layout} />
        <GraphQueryInput
          items={graph}
          value={query}
          onChange={q => this.setState({ query: q })}
          presets={interestingQueriesFor(metadata, layout)}
        />
      </GaantChartContainer>
    );
  }
}

interface GaantChartTimescaleProps {
  scale: number;
  scrollLeft: number;
  startMs: number;
  highlightedMs: number[];
}

const GaantChartTimescale = ({
  scale,
  scrollLeft,
  startMs,
  highlightedMs
}: GaantChartTimescaleProps) => {
  const viewportWidth = 1000;

  const pxPerMs = scale;
  const msPerTick = 1000 * (scale < 0.1 ? 5 : scale < 0.2 ? 1 : 0.5);
  const pxPerTick = msPerTick * pxPerMs;
  const transform = `translate(${LEFT_INSET - scrollLeft}px)`;

  const ticks: React.ReactChild[] = [];
  const lines: React.ReactChild[] = [];

  const labelPrecision = scale < 0.2 ? 0 : 1;
  const labelForTime = (ms: number, precision: number = labelPrecision) =>
    `${Number(ms / 1000).toFixed(precision)}s`;

  const firstTickX = Math.floor(scrollLeft / pxPerTick) * pxPerTick;

  for (let x = firstTickX; x < firstTickX + viewportWidth; x += pxPerTick) {
    if (x - scrollLeft < 10) continue;
    const label = labelForTime(x / pxPerMs);
    lines.push(
      <div className="line" key={label} style={{ left: x, transform }} />
    );
    ticks.push(
      <div className="tick" key={label} style={{ left: x - 20, transform }}>
        {label}
      </div>
    );
  }

  return (
    <TimescaleContainer>
      <div style={{ height: 20 }}>
        {ticks}
        {highlightedMs.map((ms, idx) => (
          <div
            key={`highlight-${idx}`}
            className="tick highlight"
            style={{
              left: (ms - startMs) * pxPerMs + (idx === 0 ? -39 : 0),
              transform
            }}
          >
            {labelForTime(ms - startMs, 3)}
          </div>
        ))}
      </div>
      <div
        style={{
          zIndex: 0,
          height: "100%",
          width: "100%",
          position: "absolute",
          pointerEvents: "none"
        }}
      >
        {lines}
        {highlightedMs.map((ms, idx) => (
          <div
            className="line highlight"
            key={`highlight-${idx}`}
            style={{ left: (ms - startMs) * pxPerMs, transform }}
          />
        ))}
      </div>
    </TimescaleContainer>
  );
};

const GaantChartContent = (
  props: GaantChartProps & GaantChartState & { layout: GaantChartLayout }
) => {
  const [scrollLeft, setScrollLeft] = React.useState<number>(0);
  const [hoveredIdx, setHoveredIdx] = React.useState<number>(-1);
  const { options, layout, metadata = { steps: {} } } = props;

  const items: React.ReactChild[] = [];
  const hovered = layout.boxes[hoveredIdx];

  layout.boxes.forEach((box, idx) => {
    const highlighted = hovered === box || hovered?.children.includes(box);
    const color = boxColorFor(box.node, metadata);

    items.push(
      <div
        key={box.node.name}
        style={{
          left: box.x,
          top: BOX_HEIGHT * box.y + BOX_MARGIN_Y,
          width: box.width,
          background: `${color} linear-gradient(180deg, rgba(255,255,255,0.15), rgba(0,0,0,0.1))`
        }}
        className={`box ${highlighted && "highlighted"}`}
        onClick={() => props.onApplyStepFilter?.(box.node.name)}
        onMouseEnter={() => setHoveredIdx(idx)}
        onMouseLeave={() => setHoveredIdx(-1)}
      >
        {box.node.name}
      </div>
    );
    if (options.mode !== GaantChartMode.FLAT) {
      box.children.forEach((child, childIdx) => {
        const childIsRendered = layout.boxes.includes(child);
        items.push(
          <GaantLine
            highlighted={hovered && (hovered === box || hovered === child)}
            dotted={!childIsRendered}
            key={`${box.node.name}-${child.node.name}-${childIdx}`}
            start={box}
            end={child}
            depIdx={childIdx}
          />
        );
      });
    }
  });

  return (
    <>
      {options.mode === GaantChartMode.WATERFALL_TIMED && (
        <GaantChartTimescale
          scale={options.scale}
          scrollLeft={scrollLeft}
          startMs={metadata.minStepStart || 0}
          highlightedMs={
            hovered
              ? ([
                  metadata.steps[hovered.node.name]?.start,
                  metadata.steps[hovered.node.name]?.finish
                ].filter(Number) as number[])
              : []
          }
        />
      )}
      <div
        style={{ overflow: "scroll", flex: 1 }}
        onScroll={e => setScrollLeft(e.currentTarget.scrollLeft)}
      >
        <div style={{ position: "relative" }}>{items}</div>
      </div>
    </>
  );
};

const GaantLine = React.memo(
  ({
    start,
    end,
    dotted,
    highlighted,
    depIdx
  }: {
    start: GaantChartBox;
    end: GaantChartBox;
    dotted: boolean;
    highlighted: boolean;
    depIdx: number;
  }) => {
    const startIdx = start.y;
    const endIdx = end.y;

    const minIdx = Math.min(startIdx, endIdx);
    const maxIdx = Math.max(startIdx, endIdx);

    const maxY = maxIdx * BOX_HEIGHT + BOX_MARGIN_Y;
    const minY = minIdx * BOX_HEIGHT + BOX_HEIGHT / 2;

    const minX = Math.min(start.x + start.width, end.x + end.width);
    const maxX =
      maxIdx === minIdx
        ? Math.max(start.x, end.x)
        : Math.max(start.x + start.width / 2, end.x + end.width / 2);

    const border = `${LINE_SIZE}px ${dotted ? "dotted" : "solid"} ${
      highlighted ? Colors.DARK_GRAY1 : Colors.LIGHT_GRAY3
    }`;

    return (
      <>
        <div
          className="line"
          data-info={`from ${start.node.name} to ${end.node.name}`}
          style={{
            height: 1,
            left: minX,
            width: dotted ? 50 : maxX + (depIdx % 10) * LINE_SIZE - minX,
            top: minY - 1,
            borderTop: border,
            zIndex: highlighted ? 100 : 1
          }}
        />
        {maxIdx !== minIdx && !dotted && (
          <div
            className="line"
            data-info={`from ${start.node.name} to ${end.node.name}`}
            style={{
              width: 1,
              left: maxX + (depIdx % 10) * LINE_SIZE,
              top: minY,
              height: maxY - minY,
              borderRight: border,
              zIndex: highlighted ? 100 : 1
            }}
          />
        )}
      </>
    );
  }
);

// Note: It is much faster to use standard CSS class selectors here than make
// each box and line a styled-component because all styled components register
// listeners for the "theme" React context.
const GaantChartContainer = styled.div`
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  z-index: 2;
  background: ${Colors.WHITE};

  .line {
    position: absolute;
    user-select: none;
    pointer-events: none;
    transition: top 200ms linear, left 200ms linear, width 200ms linear,
      height 200ms linear;
  }

  .box {
    display: inline-block;
    position: absolute;
    height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
    color: white;
    padding: 2px;
    font-size: 11px;
    border: 1px solid transparent;
    overflow: hidden;
    z-index: 2;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    border-radius: 2px;

    transition: top 200ms linear, left 200ms linear, width 200ms linear,
      height 200ms linear;

    &.highlighted {
      border: 1px solid ${Colors.DARK_GRAY1};
    }
  }
`;

const OptionsContainer = styled.div`
  height: 40px;
  display: flex;
  align-items: center;
  padding: 5px 15px;
  border-bottom: 1px solid #A7B6C2;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  background: ${Colors.WHITE};
  flex-shrink: 0;
  z-index: 3;
}`;

const OptionsDivider = styled.div`
  width: 1px;
  height: 25px;
  padding-left: 7px;
  margin-left: 7px;
  border-left: 1px solid ${Colors.LIGHT_GRAY3};
`;

const TimescaleContainer = styled.div`
  width: 100%;

  & .tick {
    position: absolute;
    padding-top: 3px;
    width: 40px;
    height: 20px;
    box-sizing: border-box;
    transition: left 200ms linear;
    text-align: center;
    font-size: 11px;
  }
  & .tick.highlight {
    color: white;
    background: red;
  }
  & .line {
    position: absolute;
    border-left: 1px solid #eee;
    transition: left 200ms linear;
    top: 0px;
    bottom: 0px;
  }
  & .line.highlight {
    border-left: 1px solid red;
  }
`;
