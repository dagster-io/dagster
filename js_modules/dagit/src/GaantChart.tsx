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
  mode: GaantChartLayoutMode;
  scale: number;
  hideWaiting: boolean;
}

export enum GaantChartLayoutMode {
  FLAT = "flat",
  WATERFALL = "waterfall",
  WATERFALL_TIMED = "waterfall-timed"
}

const BOX_HEIGHT = 30;
const BOX_MARGIN_Y = 5;
const BOX_MARGIN_X = 10;
const BOX_WIDTH = 100;
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
  metadata: IRunMetadataDict,
  options: GaantChartLayoutOptions
) => {
  const stepInfo = metadata.steps[step.name] || {};
  if (options.mode === GaantChartLayoutMode.WATERFALL_TIMED) {
    const width =
      stepInfo.finish && stepInfo.start
        ? stepInfo.finish - stepInfo.start
        : stepInfo.start
        ? Date.now() - stepInfo.start
        : BOX_WIDTH;
    return Math.max(BOX_MARGIN_X * 2, width * options.scale);
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

const buildLayout = (
  solidGraph: IGaantNode[],
  metadata: IRunMetadataDict,
  options: GaantChartLayoutOptions
) => {
  const hasNoDependencies = (g: IGaantNode) =>
    !g.inputs.some(i =>
      i.dependsOn.some(s => solidGraph.find(o => o.name === s.solid.name))
    );

  let boxes: GaantChartBox[] = solidGraph
    .filter(hasNoDependencies)
    .map(solid => ({
      node: solid,
      children: [],
      x: 0,
      y: -1,
      width: boxWidthFor(solid, metadata, options)
    }));

  const ensureSubtreeBelow = (childIdx: number, parentIdx: number) => {
    if (parentIdx <= childIdx) {
      return;
    }
    const [child] = boxes.splice(childIdx, 1);
    boxes.push(child);
    const newIdx = boxes.length - 1;
    for (const subchild of child.children) {
      ensureSubtreeBelow(boxes.indexOf(subchild), newIdx);
    }
  };

  const addChildren = (box: GaantChartBox) => {
    const idx = boxes.indexOf(box);
    const seen: string[] = [];

    for (const out of box.node.outputs) {
      for (const dep of out.dependedBy) {
        const depSolid = solidGraph.find(n => dep.solid.name === n.name);
        if (!depSolid) continue;

        if (seen.includes(depSolid.name)) continue;
        seen.push(depSolid.name);

        const depBoxIdx = boxes.findIndex(r => r.node === depSolid);
        let depBox: GaantChartBox;

        if (depBoxIdx === -1) {
          depBox = {
            children: [],
            node: depSolid,
            width: boxWidthFor(depSolid, metadata, options),
            x: 0,
            y: -1
          };
          boxes.push(depBox);
          addChildren(depBox);
        } else {
          depBox = boxes[depBoxIdx];
          ensureSubtreeBelow(depBoxIdx, idx);
        }

        box.children.push(depBox);
      }
    }
  };

  const roots = [...boxes];

  roots.forEach(addChildren);

  const deepen = (box: GaantChartBox, x: number) => {
    box.x = Math.max(x, box.x);
    box.children.forEach(child => deepen(child, x + box.width));
  };
  roots.forEach(box => deepen(box, 0));

  // now assign Y values
  if (options.mode === GaantChartLayoutMode.FLAT) {
    boxes.forEach((box, idx) => {
      box.y = idx;
      box.width = 400;
      box.x *= 0.1;
    });
  } else {
    const parents: { [name: string]: GaantChartBox[] } = {};
    const boxesByY: { [y: string]: GaantChartBox[] } = {};

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

    // reflow to fill empty rows
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

  // apply display options
  if (
    options.mode === GaantChartLayoutMode.WATERFALL_TIMED &&
    options.hideWaiting
  ) {
    boxes = boxes.filter(b => {
      const state = metadata.steps[b.node.name]?.state || "waiting";
      return state !== "waiting";
    });
  }

  return { boxes } as GaantChartLayout;
};

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
          mode: GaantChartLayoutMode.WATERFALL,
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
    const layout = buildLayout(graphFiltered.all, metadata, options);

    // todo perf: We can break buildLayout into a function that does not need metadata
    // and then a post-processor that resizes/shifts things using `metadata`. Then we can
    // memoize the time consuming vertical layout work.

    const setOptions = (changes: Partial<GaantChartLayoutOptions>) => {
      this.setState({ ...this.state, options: { ...options, ...changes } });
    };

    return (
      <GaantChartContainer>
        <OptionsContainer>
          <ButtonGroup style={{ flexShrink: 0 }}>
            {[
              GaantChartLayoutMode.FLAT,
              GaantChartLayoutMode.WATERFALL,
              GaantChartLayoutMode.WATERFALL_TIMED
            ].map(mode => (
              <Button
                key={mode}
                text={mode.toLowerCase()}
                small={true}
                active={options.mode === mode}
                onClick={() =>
                  setOptions({ mode: mode as GaantChartLayoutMode })
                }
              />
            ))}
          </ButtonGroup>
          {options.mode === GaantChartLayoutMode.WATERFALL_TIMED && (
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
        <div style={{ overflow: "scroll", flex: 1 }}>
          <GaantChartContent {...this.props} {...this.state} layout={layout} />
        </div>
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

const GaantChartContent = (
  props: GaantChartProps & GaantChartState & { layout: GaantChartLayout }
) => {
  const [hoveredIdx, setHoveredIdx] = React.useState<number>(-1);
  const { options, layout, metadata = { steps: {} } } = props;

  const items: React.ReactChild[] = [];
  const hovered = layout.boxes[hoveredIdx];

  layout.boxes.forEach((box, idx) => {
    const highlighted = hovered === box || hovered?.children.includes(box);

    items.push(
      <div
        key={box.node.name}
        style={{
          left: box.x + BOX_MARGIN_X,
          top: BOX_HEIGHT * box.y + BOX_MARGIN_Y,
          width: Math.max(1, box.width - BOX_MARGIN_X * 2),
          background: boxColorFor(box.node, metadata)
        }}
        className={`box ${highlighted && "highlighted"}`}
        onClick={() => props.onApplyStepFilter?.(box.node.name)}
        onMouseEnter={() => setHoveredIdx(idx)}
        onMouseLeave={() => setHoveredIdx(-1)}
      >
        {box.node.name}
      </div>
    );
    if (options.mode !== GaantChartLayoutMode.FLAT) {
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

  return <div style={{ position: "relative" }}>{items}</div>;
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

    const minX =
      Math.min(start.x + start.width, end.x + start.width) - BOX_MARGIN_X + 1;
    const maxX =
      maxIdx === minIdx
        ? Math.max(start.x, end.x) + BOX_MARGIN_X
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
}`;
