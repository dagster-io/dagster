import * as React from "react";
import styled from "styled-components/macro";
import { weakmapMemoize } from "./Util";
import { ILayoutSolid } from "./graph/layout";
import { IRunMetadataDict } from "./RunMetadataProvider";
import { ExecutionPlanFragment } from "./plan/types/ExecutionPlanFragment";
import { RunFragment } from "./runs/types/RunFragment";
import { GraphQueryInput } from "./GraphQueryInput";
import { filterByQuery } from "./GraphQueryImpl";

interface GaantChartProps {
  metadata: IRunMetadataDict;
  plan: ExecutionPlanFragment;
  run: RunFragment;
}

interface GaantChartRow {
  depth: number;
  children: GaantChartRow[];
  solid: ILayoutSolid;
}
interface GaantChartLayout {
  rows: GaantChartRow[];
}

const ROW_HEIGHT = 20;
const BOX_WIDTH = 80;
const LINE_SIZE = 2;

const toMockSolidGraph = weakmapMemoize((run: RunFragment) => {
  if (!run.executionPlan) {
    throw new Error("tld");
  }
  const solidsTable: { [key: string]: ILayoutSolid } = {};

  for (const step of run.executionPlan.steps) {
    const solid: ILayoutSolid = {
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

const forEachDep = (solid: ILayoutSolid, cb: (name: string) => void) => {
  for (const out of solid.outputs) {
    for (const dep of out.dependedBy) {
      cb(dep.solid.name);
    }
  }
};

const collapseRunsInSolidGraph = (
  solidGraph: ILayoutSolid[],
  solidNames: string[]
) => {
  solidGraph = JSON.parse(JSON.stringify(solidGraph));

  for (const name of solidNames) {
    // find the node
    const solid = solidGraph.find(s => s.name === name);
    if (!solid) continue;

    // merge the node with it's immediate children
    const nextSet: string[] = [];
    forEachDep(solid, childName => {
      const childSolidIdx = solidGraph.findIndex(s => s.name === childName);
      if (childSolidIdx === -1) return;
      const [childSolid] = solidGraph.splice(childSolidIdx, 1);
      forEachDep(childSolid, name => {
        nextSet.push(name);
      });
    });

    if (nextSet.length) {
      solid.outputs[0].definition.name = "COLLAPSED";
      solid.outputs[0].dependedBy = nextSet.map(m => ({
        solid: { name: m },
        definition: { name: "" }
      }));
    }
  }

  return solidGraph;
};

const layout = (solidGraph: ILayoutSolid[]) => {
  let rows: GaantChartRow[] = solidGraph
    .filter(
      g =>
        g.inputs.filter(i =>
          i.dependsOn.some(s => solidGraph.find(o => o.name === s.solid.name))
        ).length === 0
    )
    .map(solid => ({ solid: solid, children: [], depth: 0 }));

  let rowZero = [...rows];

  const ensureSubtreeBelow = (childIdx: number, parentIdx: number) => {
    if (parentIdx < childIdx) {
      return;
    }
    const [child] = rows.splice(childIdx, 1);
    rows.push(child);
    const newIdx = rows.length - 1;
    child.children.forEach(subchild =>
      ensureSubtreeBelow(rows.indexOf(subchild), newIdx)
    );
  };

  const addChildren = (row: GaantChartRow) => {
    const idx = rows.indexOf(row);
    const seen: string[] = [];

    for (const out of row.solid.outputs) {
      for (const dep of out.dependedBy) {
        const depSolid = solidGraph.find(n => dep.solid.name === n.name);
        if (!depSolid) continue;

        if (seen.includes(depSolid.name)) continue;
        seen.push(depSolid.name);

        const depRowIdx = rows.findIndex(r => r.solid === depSolid);
        let depRow: GaantChartRow;

        if (depRowIdx === -1) {
          depRow = {
            solid: depSolid,
            depth: 0,
            children: []
          };
          rows.push(depRow);
          addChildren(depRow);
        } else {
          depRow = rows[depRowIdx];
          ensureSubtreeBelow(depRowIdx, idx);
        }

        row.children.push(depRow);
      }
    }
  };

  rowZero.forEach(addChildren);

  const deepen = (row: GaantChartRow, depth: number) => {
    row.depth = Math.max(depth, row.depth);
    row.children.forEach(child => deepen(child, depth + 1));
  };
  rowZero.forEach(row => deepen(row, 0));

  return { rows } as GaantChartLayout;
};

interface GaantChartState {
  hoveredIdx: number;
  query: string;
  collapsed: string[];
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  state: GaantChartState = {
    hoveredIdx: -1,
    collapsed: [],
    query: "*trials_raw"
  };

  render() {
    const { hoveredIdx, query, collapsed } = this.state;

    const graph = toMockSolidGraph(this.props.run);
    const graphFiltered = filterByQuery(graph, query);
    const graphCollapsed = collapseRunsInSolidGraph(
      graphFiltered.all,
      collapsed
    );
    const l = layout(graphCollapsed);

    return (
      <div style={{ height: "100%" }}>
        <div style={{ overflow: "scroll", height: "100%" }}>
          <div style={{ position: "relative" }}>
            {l.rows.map((row, idx) => (
              <React.Fragment key={row.solid.name}>
                <GaantBox
                  style={{
                    top: ROW_HEIGHT * idx,
                    left: row.depth * BOX_WIDTH,
                    width: BOX_WIDTH
                  }}
                  collapsed={
                    row.solid.outputs[0]?.definition.name === "COLLAPSED"
                  }
                  onMouseEnter={() => this.setState({ hoveredIdx: idx })}
                  onMouseLeave={() => this.setState({ hoveredIdx: -1 })}
                  onClick={() =>
                    this.setState({
                      collapsed: collapsed.includes(row.solid.name)
                        ? collapsed.filter(c => c !== row.solid.name)
                        : [...collapsed, row.solid.name]
                    })
                  }
                >
                  {row.solid.name}
                </GaantBox>
                {row.children.map((child, childIdx) => {
                  const childRowIdx = l.rows.indexOf(child);
                  return (
                    <GaantLine
                      key={`${row.solid.name}-${child.solid.name}-${childIdx}`}
                      rows={l.rows}
                      start={row}
                      end={child}
                      depIdx={childIdx}
                      highlighted={
                        hoveredIdx === idx || hoveredIdx === childRowIdx
                      }
                    />
                  );
                })}
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

const GaantLine = React.memo(
  (props: {
    rows: GaantChartRow[];
    start: GaantChartRow;
    end: GaantChartRow;
    highlighted: boolean;
    depIdx: number;
  }) => {
    const minDepth = Math.min(props.start.depth, props.end.depth);
    const maxDepth = Math.max(props.start.depth, props.end.depth);

    const startIdx = props.rows.indexOf(props.start);
    const endIdx = props.rows.indexOf(props.end);
    const minIdx = Math.min(startIdx, endIdx);
    const maxIdx = Math.max(startIdx, endIdx);

    if (minIdx === -1) {
      console.warn("Row missing");
    }
    if (minDepth === maxDepth) {
      console.warn("minDepth === maxDepth");
    }
    if (minIdx === maxIdx) {
      console.warn("minIdx === maxIdx");
    }

    const offsetX = BOX_WIDTH / 2;
    const maxX = maxDepth * BOX_WIDTH + offsetX;
    const minX = (minDepth + 1) * BOX_WIDTH;
    const maxY = maxIdx * ROW_HEIGHT;
    const minY = minIdx * ROW_HEIGHT + ROW_HEIGHT / 2;

    return (
      <>
        <Line
          data-info={`from ${props.start.solid.name} to ${props.end.solid.name}`}
          style={{
            height: LINE_SIZE,
            left: minX,
            width: maxX - minX,
            top: minY,
            background: props.highlighted ? "red" : "#eee",
            zIndex: props.highlighted ? 100 : 1
          }}
        />
        <Line
          data-info={`from ${props.start.solid.name} to ${props.end.solid.name}`}
          style={{
            width: LINE_SIZE,
            left: maxX + props.depIdx * LINE_SIZE,
            top: minY,
            height: maxY - minY,
            background: props.highlighted ? "red" : "#eee",
            zIndex: props.highlighted ? 100 : 1
          }}
        />
      </>
    );
  }
);

const Line = styled.div`
  position: absolute;
  transition: top 200ms linear, left 200ms linear, width 200ms linear,
    height 200ms linear;
`;

const GaantRow = styled.div`
  display: block;
  height: ${ROW_HEIGHT}px;
  border-bottom: 1px solid #ccc;
`;

const GaantBox = styled.div<{ collapsed: boolean }>`
  display: inline-block;
  position: absolute;
  height: ${ROW_HEIGHT}px;
  background: ${({ collapsed }) => (collapsed ? "#1c71bc" : "#2491eb")};
  color: white;
  font-size: 11px;
  border: 1px solid darkgreen;
  overflow: hidden;
  z-index: 2;

  transition: top 200ms linear, left 200ms linear, width 200ms linear,
    height 200ms linear;
`;
