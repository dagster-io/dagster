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
  y: number;
}
interface GaantChartLayout {
  rows: GaantChartRow[];
}

const ROW_HEIGHT = 30;
const ROW_MARGIN = 5;
const BOX_WIDTH = 100;
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

const layout = (solidGraph: ILayoutSolid[], steps: number) => {
  let rows: GaantChartRow[] = solidGraph
    .filter(
      g =>
        g.inputs.filter(i =>
          i.dependsOn.some(s => solidGraph.find(o => o.name === s.solid.name))
        ).length === 0
    )
    .map(solid => ({ solid: solid, children: [], depth: 0, y: -1 }));

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
            children: [],
            y: -1
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

  // now assign Y values
  const parents: { [name: string]: GaantChartRow[] } = {};
  rows.forEach((row, idx) => {
    row.y = idx;
    row.children.forEach(child => {
      parents[child.solid.name] = parents[child.solid.name] || [];
      parents[child.solid.name].push(row);
    });
  });

  let changed = true;
  while (changed) {
    changed = false;
    for (let idx = rows.length - 1; idx > 0; idx--) {
      const row = rows[idx];
      const rowParents = parents[row.solid.name] || [];
      const highestYParent = rowParents.sort((a, b) => b.y - a.y)[0];
      if (!highestYParent) continue;

      const onTargetY = rows.filter(r => r.y === highestYParent.y);
      const taken = onTargetY.find(r => r.depth === row.depth);
      if (taken) continue;

      const parentDepth = highestYParent.depth;
      const willCross = onTargetY.some(
        r => r.depth > parentDepth && r.depth < row.depth
      );
      const willCauseCrossing = onTargetY.some(
        r =>
          r.depth < row.depth &&
          r.children.some(c => c.y >= highestYParent.y && c.depth > row.depth)
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
    let maxY = rows.reduce((m, r) => Math.max(m, r.y), 0);
    for (let y = 0; y < maxY; y++) {
      const empty = !rows.some(r => r.y === y);
      if (empty) {
        rows.filter(r => r.y > y).forEach(r => (r.y -= 1));
        changed = true;
        break;
      }
    }
  }

  return { rows } as GaantChartLayout;
};

interface GaantChartState {
  hoveredIdx: number;
  query: string;
  collapsed: string[];
  n: number;
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  state: GaantChartState = {
    hoveredIdx: -1,
    collapsed: [],
    query: "*trials_raw",
    n: 100
  };

  render() {
    const { hoveredIdx, query, collapsed, n } = this.state;

    const graph = toMockSolidGraph(this.props.run);
    const graphFiltered = filterByQuery(graph, query);
    const graphCollapsed = collapseRunsInSolidGraph(
      graphFiltered.all,
      collapsed
    );
    const l = layout(graphCollapsed, n);

    return (
      <div style={{ height: "100%" }}>
        <div onClick={() => this.setState({ n: n + 1 })}>+1</div>
        <div onClick={() => this.setState({ n: n - 1 })}>-1</div>
        <div>{n}</div>
        <div style={{ overflow: "scroll", height: "100%" }}>
          <div style={{ position: "relative" }}>
            {l.rows.map((row, idx) => (
              <React.Fragment key={row.solid.name}>
                <GaantBox
                  key={row.solid.name}
                  style={{
                    top: ROW_HEIGHT * row.y + 5,
                    left: row.depth * BOX_WIDTH + 10,
                    width: BOX_WIDTH - 20
                  }}
                  collapsed={
                    row.solid.outputs[0]?.definition.name === "COLLAPSED"
                  }
                  highlighted={
                    hoveredIdx === idx ||
                    l.rows[hoveredIdx]?.children.includes(row)
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
                {row.children.map((child, childIdx) => (
                  <GaantLine
                    key={`${row.solid.name}-${child.solid.name}-${childIdx}`}
                    rows={l.rows}
                    start={row}
                    end={child}
                    depIdx={childIdx}
                    highlighted={
                      hoveredIdx === idx || hoveredIdx === l.rows.indexOf(child)
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

const GaantLine = (props: {
  rows: GaantChartRow[];
  start: GaantChartRow;
  end: GaantChartRow;
  highlighted: boolean;
  depIdx: number;
}) => {
  const minDepth = Math.min(props.start.depth, props.end.depth);
  const maxDepth = Math.max(props.start.depth, props.end.depth);

  const startIdx = props.start.y; //props.rows.indexOf(props.start);
  const endIdx = props.end.y; //.indexOf(props.end);
  const minIdx = Math.min(startIdx, endIdx);
  const maxIdx = Math.max(startIdx, endIdx);

  const offsetX = maxIdx === minIdx ? 0 : 80 / 2;
  const maxY = maxIdx * ROW_HEIGHT + ROW_MARGIN;
  const minY = minIdx * ROW_HEIGHT + ROW_HEIGHT / 2;
  const maxX = maxDepth * BOX_WIDTH + offsetX + 10;
  const minX = (minDepth + 1) * BOX_WIDTH - 10;

  return (
    <>
      <Line
        data-info={`from ${props.start.solid.name} to ${props.end.solid.name}`}
        style={{
          height: LINE_SIZE,
          left: minX,
          width: maxX + (props.depIdx % 10) * LINE_SIZE - minX,
          top: minY,
          background: props.highlighted ? "red" : "#eee",
          zIndex: props.highlighted ? 100 : 1
        }}
      />
      {maxIdx !== minIdx && (
        <Line
          data-info={`from ${props.start.solid.name} to ${props.end.solid.name}`}
          style={{
            width: LINE_SIZE,
            left: maxX + (props.depIdx % 10) * LINE_SIZE,
            top: minY,
            height: maxY - minY,
            background: props.highlighted ? "red" : "#eee",
            zIndex: props.highlighted ? 100 : 1
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

const GaantRow = styled.div`
  display: block;
  height: ${ROW_HEIGHT}px;
  border-bottom: 1px solid #ccc;
`;

const GaantBox = styled.div<{ collapsed: boolean; highlighted: boolean }>`
  display: inline-block;
  position: absolute;
  height: ${ROW_HEIGHT - ROW_MARGIN * 2}px;
  background: ${({ collapsed, highlighted }) =>
    highlighted ? "red" : collapsed ? "#1c71bc" : "#2491eb"};
  color: white;
  font-size: 11px;
  border: 1px solid darkgreen;
  overflow: hidden;
  z-index: 2;

  transition: top 200ms linear, left 200ms linear, width 200ms linear,
    height 200ms linear;
`;
