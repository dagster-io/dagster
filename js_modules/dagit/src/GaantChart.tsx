import * as React from "react";
import styled from "styled-components/macro";
import { weakmapMemoize } from "./Util";
import { layoutPipeline, ILayoutSolid } from "./graph/layout";
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
  x: number;
  depth: number;
  dependencies: GaantChartRow[];
  label: string;
}
interface GaantChartLayout {
  rows: GaantChartRow[];
}

const ROW_HEIGHT = 20;
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

const layout = weakmapMemoize((solidGraph: ILayoutSolid[]) => {
  const stepInputKeys: { [key: string]: string[] } = {};

  for (const solid of solidGraph) {
    stepInputKeys[solid.name] = [];
    for (const input of solid.inputs) {
      stepInputKeys[solid.name].push(...input.dependsOn.map(d => d.solid.name));
    }
  }
  const layout = layoutPipeline(solidGraph);

  // arrange in order of Y
  const rows: GaantChartRow[] = [];
  let depth = 0;
  let lastY = 0;

  Object.entries(layout.solids)
    .sort((a, b) => {
      const yDiff = a[1].boundingBox.y - b[1].boundingBox.y;
      if (yDiff != 0) return yDiff;
      const xDiff = a[1].boundingBox.x - b[1].boundingBox.x;
      return xDiff;
    })
    .forEach(([key, solid]) => {
      if (Math.abs(lastY - solid.boundingBox.y) > 50) {
        lastY = solid.boundingBox.y;
        depth += 1;
      }
      rows.push({
        x: depth * 50,
        depth: depth,
        dependencies: rows.filter(r => stepInputKeys[key].includes(r.label)),
        label: key
      });
    });

  return { rows } as GaantChartLayout;
});

interface GaantChartState {
  hoveredIdx: number;
  query: string;
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  state: GaantChartState = {
    hoveredIdx: -1,
    query: "*"
  };

  render() {
    const { hoveredIdx, query } = this.state;

    const graph = toMockSolidGraph(this.props.run);
    const graphFiltered = filterByQuery(graph, query);
    const l = layout(graphFiltered.all);

    return (
      <div style={{ height: "100%" }}>
        <div style={{ overflow: "scroll", height: "100%" }}>
          <div style={{ position: "relative" }}>
            {l.rows.map((row, idx) => (
              <React.Fragment key={row.label}>
                <GaantBox
                  style={{
                    top: ROW_HEIGHT * idx,
                    left: row.depth * 50,
                    width: 50
                  }}
                  onMouseEnter={() => this.setState({ hoveredIdx: idx })}
                  onMouseLeave={() => this.setState({ hoveredIdx: -1 })}
                >
                  {row.label}
                </GaantBox>
                {row.dependencies
                  .filter(
                    dep =>
                      hoveredIdx === idx || hoveredIdx === l.rows.indexOf(dep)
                  )
                  .map((dep, depIdx) => (
                    <>
                      <Line
                        key={`${idx}-${depIdx}-horizontal`}
                        style={{
                          height: LINE_SIZE,
                          left: (dep.depth + 1) * 50,
                          width:
                            row.depth * 50 -
                            (dep.depth + 1) * 50 +
                            20 +
                            depIdx * LINE_SIZE,
                          top:
                            l.rows.indexOf(dep) * ROW_HEIGHT + ROW_HEIGHT / 2,
                          background: "red"
                        }}
                      />
                      <Line
                        key={`${idx}-${depIdx}-vertical`}
                        style={{
                          width: LINE_SIZE,
                          left: row.depth * 50 + 20 + depIdx * LINE_SIZE,
                          top:
                            l.rows.indexOf(dep) * ROW_HEIGHT + ROW_HEIGHT / 2,
                          height:
                            idx * ROW_HEIGHT -
                            l.rows.indexOf(dep) * ROW_HEIGHT -
                            ROW_HEIGHT / 2,
                          background: "red"
                        }}
                      />
                    </>
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

const Line = styled.div`
  position: absolute;
`;

const GaantRow = styled.div`
  display: block;
  height: ${ROW_HEIGHT}px;
  border-bottom: 1px solid #ccc;
`;

const GaantBox = styled.div`
  display: inline-block;
  position: absolute;
  height: ${ROW_HEIGHT}px;
  background: green;
  color: white;
  font-size: 11px;
  border: 1px solid darkgreen;
`;
