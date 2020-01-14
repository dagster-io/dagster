import * as React from "react";
import styled from "styled-components/macro";
import { weakmapMemoize } from "./Util";
import { IRunMetadataDict } from "./RunMetadataProvider";
import { ExecutionPlanFragment } from "./plan/types/ExecutionPlanFragment";
import { RunFragment } from "./runs/types/RunFragment";
import { GraphQueryInput } from "./GraphQueryInput";
import { filterByQuery, GraphQueryItem } from "./GraphQueryImpl";
import { Slider, ButtonGroup, Button, Colors } from "@blueprintjs/core";

type IGaantNode = GraphQueryItem;

interface GaantChartProps {
  metadata: IRunMetadataDict;
  plan: ExecutionPlanFragment;
  run: RunFragment;
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

enum GaantChartLayoutMode {
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
const toGraphQueryItems = weakmapMemoize((run: RunFragment) => {
  if (!run.executionPlan) {
    throw new Error("tld");
  }
  const nodeTable: { [key: string]: IGaantNode } = {};

  for (const step of run.executionPlan.steps) {
    const node: IGaantNode = {
      name: step.key,
      inputs: [],
      outputs: []
    };
    nodeTable[step.key] = node;
  }

  for (const step of run.executionPlan.steps) {
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
});

const boxWidthFor = (
  step: GraphQueryItem,
  metadata: IRunMetadataDict,
  options: GaantChartLayoutOptions
) => {
  const stepInfo = metadata.steps[step.name] || {};
  if (options.mode === GaantChartLayoutMode.WATERFALL_TIMED) {
    return (
      10 +
      (stepInfo.finish && stepInfo.start
        ? Math.max(0, stepInfo.finish - stepInfo.start) * options.scale
        : BOX_WIDTH * options.scale)
    );
  }
  return BOX_WIDTH;
};

const boxColorFor = (
  step: GraphQueryItem,
  metadata: IRunMetadataDict,
  options: GaantChartLayoutOptions
) => {
  const stepInfo = metadata.steps[step.name] || {};
  if (options.mode === GaantChartLayoutMode.WATERFALL_TIMED) {
    return (
      {
        running: Colors.GRAY3,
        succeeded: Colors.GREEN2,
        skipped: Colors.GOLD3,
        failed: Colors.RED3
      }[stepInfo.state] || Colors.GRAY1
    );
  }
  return "#2491eb";
};

const layout = (
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
    if (parentIdx < childIdx) {
      return;
    }
    const [child] = boxes.splice(childIdx, 1);
    boxes.push(child);
    const newIdx = boxes.length - 1;
    child.children.forEach(subchild =>
      ensureSubtreeBelow(boxes.indexOf(subchild), newIdx)
    );
  };

  const addChildren = (row: GaantChartBox) => {
    const idx = boxes.indexOf(row);
    const seen: string[] = [];

    for (const out of row.node.outputs) {
      for (const dep of out.dependedBy) {
        const depSolid = solidGraph.find(n => dep.solid.name === n.name);
        if (!depSolid) continue;

        if (seen.includes(depSolid.name)) continue;
        seen.push(depSolid.name);

        const depRowIdx = boxes.findIndex(r => r.node === depSolid);
        let depRow: GaantChartBox;

        if (depRowIdx === -1) {
          depRow = {
            children: [],
            node: depSolid,
            width: BOX_WIDTH,
            x: 0,
            y: -1
          };
          boxes.push(depRow);
          addChildren(depRow);
        } else {
          depRow = boxes[depRowIdx];
          ensureSubtreeBelow(depRowIdx, idx);
        }

        row.children.push(depRow);
      }
    }
  };

  const roots = [...boxes];

  roots.forEach(addChildren);

  const deepen = (row: GaantChartBox, x: number) => {
    row.x = Math.max(x, row.x);
    row.children.forEach(child => deepen(child, x + row.width));
  };
  roots.forEach(row => deepen(row, 0));

  // now assign Y values
  const parents: { [name: string]: GaantChartBox[] } = {};
  boxes.forEach((row, idx) => {
    row.y = idx;
    row.children.forEach(child => {
      parents[child.node.name] = parents[child.node.name] || [];
      parents[child.node.name].push(row);
    });
  });

  let changed = true;
  while (changed) {
    changed = false;
    for (let idx = boxes.length - 1; idx > 0; idx--) {
      const row = boxes[idx];
      const rowParents = parents[row.node.name] || [];
      const highestYParent = rowParents.sort((a, b) => b.y - a.y)[0];
      if (!highestYParent) continue;

      const onTargetY = boxes.filter(r => r.y === highestYParent.y);
      const taken = onTargetY.find(r => r.x === row.x);
      if (taken) continue;

      const parentX = highestYParent.x;
      const willCross = onTargetY.some(r => r.x > parentX && r.x < row.x);
      const willCauseCrossing = onTargetY.some(
        r =>
          r.x < row.x &&
          r.children.some(c => c.y >= highestYParent.y && c.x > row.x)
      );
      if (willCross || willCauseCrossing) continue;

      row.y = highestYParent.y;
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

  // apply display options
  if (options.hideWaiting) {
    boxes = boxes.filter(b => {
      const state = metadata.steps[b.node.name]?.state || "waiting";
      return state !== "waiting";
    });
  }

  return { boxes } as GaantChartLayout;
};

interface GaantChartState {
  hoveredIdx: number;
  options: GaantChartLayoutOptions;
  query: string;
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  state: GaantChartState = {
    hoveredIdx: -1,
    query: "*trials_raw",
    options: {
      mode: GaantChartLayoutMode.WATERFALL,
      hideWaiting: true,
      scale: 0.2
    }
  };

  render() {
    const { run, metadata } = this.props;
    const { hoveredIdx, query, options } = this.state;

    const graph = toGraphQueryItems(run);
    const graphFiltered = filterByQuery(graph, query);
    const l = layout(graphFiltered.all, metadata, options);

    return (
      <div style={{ height: "100%" }}>
        <div style={{ width: 200 }}>
          <ButtonGroup>
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
                  this.setState({
                    ...this.state,
                    options: { ...options, mode: mode as GaantChartLayoutMode }
                  })
                }
              />
            ))}
          </ButtonGroup>
          <Slider
            min={0.01}
            max={1}
            stepSize={0.05}
            value={options.scale}
            onChange={v =>
              this.setState({
                ...this.state,
                options: { ...options, scale: v }
              })
            }
          />
        </div>
        <div style={{ overflow: "scroll", height: "100%" }}>
          <div style={{ position: "relative" }}>
            {l.boxes.map((box, idx) => (
              <React.Fragment key={box.node.name}>
                <GaantBox
                  key={box.node.name}
                  style={{
                    top: BOX_HEIGHT * box.y + 5,
                    left: box.x + 10,
                    width: box.width - 20
                  }}
                  highlighted={
                    hoveredIdx === idx ||
                    l.boxes[hoveredIdx]?.children.includes(box)
                  }
                  color={boxColorFor(box.node, metadata, options)}
                  onMouseEnter={() => this.setState({ hoveredIdx: idx })}
                  onMouseLeave={() => this.setState({ hoveredIdx: -1 })}
                >
                  {box.node.name}
                </GaantBox>
                {box.children.map((child, childIdx) => (
                  <GaantLine
                    key={`${box.node.name}-${child.node.name}-${childIdx}`}
                    start={box}
                    end={child}
                    depIdx={childIdx}
                    highlighted={
                      hoveredIdx === idx ||
                      hoveredIdx === l.boxes.indexOf(child)
                    }
                  />
                ))}
              </React.Fragment>
            ))}
          </div>
        </div>
        <GraphQueryInput
          items={graph}
          value={query}
          onChange={q => this.setState({ query: q })}
        />
      </div>
    );
  }
}

const GaantLine = ({
  start,
  end,
  highlighted,
  depIdx
}: {
  start: GaantChartBox;
  end: GaantChartBox;
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
    Math.min(start.x + start.width, end.x + start.width) - BOX_MARGIN_X;
  const maxX = Math.max(start.x + start.width / 2, end.x + end.width / 2);

  return (
    <>
      <Line
        data-info={`from ${start.node.name} to ${end.node.name}`}
        style={{
          height: LINE_SIZE,
          left: minX,
          width: maxX + (depIdx % 10) * LINE_SIZE - minX,
          top: minY,
          background: highlighted ? "red" : "#eee",
          zIndex: highlighted ? 100 : 1
        }}
      />
      {maxIdx !== minIdx && (
        <Line
          data-info={`from ${start.node.name} to ${end.node.name}`}
          style={{
            width: LINE_SIZE,
            left: maxX + (depIdx % 10) * LINE_SIZE,
            top: minY,
            height: maxY - minY,
            background: highlighted ? "red" : "#eee",
            zIndex: highlighted ? 100 : 1
          }}
        />
      )}
    </>
  );
};

const Line = styled.div`
  position: absolute;
  user-select: none;
  pointer-events: none;
  transition: top 200ms linear, left 200ms linear, width 200ms linear,
    height 200ms linear;
`;

const GaantBox = styled.div<{ highlighted: boolean; color: string }>`
  display: inline-block;
  position: absolute;
  height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
  background: ${({ highlighted, color }) => (highlighted ? "red" : color)};
  color: white;
  font-size: 11px;
  border: 1px solid darkgreen;
  overflow: hidden;
  z-index: 2;

  transition: top 200ms linear, left 200ms linear, width 200ms linear,
    height 200ms linear;
`;
