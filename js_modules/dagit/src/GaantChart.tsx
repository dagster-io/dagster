import * as React from "react";
import styled from "styled-components/macro";
import { weakmapMemoize } from "./Util";
import { ILayoutSolid } from "./graph/layout";
import { IRunMetadataDict } from "./RunMetadataProvider";
import { ExecutionPlanFragment } from "./plan/types/ExecutionPlanFragment";
import { RunFragment } from "./runs/types/RunFragment";
import { GraphQueryInput } from "./GraphQueryInput";
import { filterByQuery } from "./GraphQueryImpl";

type IGaantNode = ILayoutSolid;

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

const toMockSolidGraph = weakmapMemoize((run: RunFragment) => {
  if (!run.executionPlan) {
    throw new Error("tld");
  }
  const solidsTable: { [key: string]: IGaantNode } = {};

  for (const step of run.executionPlan.steps) {
    const solid: IGaantNode = {
      name: step.key,
      inputs: [],
      outputs: []
    };
    solidsTable[step.key] = solid;
  }

  for (const step of run.executionPlan.steps) {
    for (const input of step.inputs) {
      solidsTable[step.key].inputs.push({
        definition: {
          name: ""
        },
        dependsOn: input.dependsOn.map(d => ({
          definition: {
            name: ""
          },
          solid: {
            name: d.key
          }
        }))
      });

      for (const upstream of input.dependsOn) {
        let output = solidsTable[upstream.key].outputs[0];
        if (!output) {
          output = {
            definition: { name: "" },
            dependedBy: []
          };
          solidsTable[upstream.key].outputs.push(output);
        }
        output.dependedBy.push({
          definition: { name: "" },
          solid: { name: step.key }
        });
      }
    }
  }

  return Object.values(solidsTable);
});

const layout = (solidGraph: ILayoutSolid[], mode: GaantChartLayoutMode) => {
  const hasNoDependencies = (g: ILayoutSolid) =>
    !g.inputs.some(i =>
      i.dependsOn.some(s => solidGraph.find(o => o.name === s.solid.name))
    );

  const boxes: GaantChartBox[] = solidGraph
    .filter(hasNoDependencies)
    .map(solid => ({
      node: solid,
      children: [],
      x: 0,
      y: -1,
      width: BOX_WIDTH
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

  return { boxes } as GaantChartLayout;
};

interface GaantChartState {
  hoveredIdx: number;
  layoutMode: GaantChartLayoutMode;
  query: string;
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  state: GaantChartState = {
    hoveredIdx: -1,
    query: "*trials_raw",
    layoutMode: GaantChartLayoutMode.FLAT
  };

  render() {
    const { hoveredIdx, query, layoutMode } = this.state;

    const graph = toMockSolidGraph(this.props.run);
    const graphFiltered = filterByQuery(graph, query);
    const l = layout(graphFiltered.all, layoutMode);

    return (
      <div style={{ height: "100%" }}>
        <div style={{ overflow: "scroll", height: "100%" }}>
          <div style={{ position: "relative" }}>
            {l.boxes.map((row, idx) => (
              <React.Fragment key={row.node.name}>
                <GaantBox
                  key={row.node.name}
                  style={{
                    top: BOX_HEIGHT * row.y + 5,
                    left: row.x + 10,
                    width: row.width - 20
                  }}
                  highlighted={
                    hoveredIdx === idx ||
                    l.boxes[hoveredIdx]?.children.includes(row)
                  }
                  onMouseEnter={() => this.setState({ hoveredIdx: idx })}
                  onMouseLeave={() => this.setState({ hoveredIdx: -1 })}
                >
                  {row.node.name}
                </GaantBox>
                {row.children.map((child, childIdx) => (
                  <GaantLine
                    key={`${row.node.name}-${child.node.name}-${childIdx}`}
                    start={row}
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
          items={toMockSolidGraph(this.props.run)}
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
  transition: top 200ms linear, left 200ms linear, width 200ms linear,
    height 200ms linear;
`;

const GaantBox = styled.div<{ highlighted: boolean }>`
  display: inline-block;
  position: absolute;
  height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
  background: ${({ highlighted }) => (highlighted ? "red" : "#2491eb")};
  color: white;
  font-size: 11px;
  border: 1px solid darkgreen;
  overflow: hidden;
  z-index: 2;

  transition: top 200ms linear, left 200ms linear, width 200ms linear,
    height 200ms linear;
`;
