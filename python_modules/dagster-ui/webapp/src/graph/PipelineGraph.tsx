import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Card, Colors } from "@blueprintjs/core";
import { Group } from "@vx/group";
import { Graph, DefaultNode } from "@vx/network";
import { LinkHorizontalStep } from "@vx/shape";
import { LegendOrdinal } from "@vx/legend";
import { scaleOrdinal } from "@vx/scale";
import { ParentSize } from "@vx/responsive";
import {
  PipelineGraphFragment,
  PipelineGraphFragment_solids,
  PipelineGraphFragment_solids_inputs,
  PipelineGraphFragment_solids_output,
  PipelineGraphFragment_solids_inputs_sources
} from "./types/PipelineGraphFragment";

interface IPipelineGraphProps {
  pipeline: PipelineGraphFragment;
}

interface IGraphNode {
  id: string;
  x: number;
  y: number;
}

type GraphNode = IGraphNode &
  (
    | {
        type: "source";
        source: PipelineGraphFragment_solids_inputs_sources;
      }
    | {
        type: "input";
        input: PipelineGraphFragment_solids_inputs;
      }
    | {
        type: "solid";
        solid: PipelineGraphFragment_solids;
      }
    | {
        type: "output";
        output: PipelineGraphFragment_solids_output;
      });

const NodeColorsScale = scaleOrdinal({
  domain: ["source", "input", "solid", "output", "materializations"],
  range: [
    Colors.TURQUOISE5,
    Colors.TURQUOISE3,
    Colors.GRAY5,
    Colors.ORANGE3,
    Colors.ORANGE5
  ]
});

export default class PipelineGraph extends React.Component<
  IPipelineGraphProps,
  {}
> {
  static fragments = {
    PipelineGraphFragment: gql`
      fragment PipelineGraphFragment on Pipeline {
        solids {
          name
          inputs {
            name
            sources {
              name: sourceType
            }
            dependsOn {
              name
            }
          }
          output {
            materializations {
              name
            }
            expectations {
              name
              description
            }
          }
        }
      }
    `
  };

  render() {
    // So this is a very naive positioning algorithm, it might result in bad
    // visualiasation. When someone is brave, they can do
    // https://en.wikipedia.org/wiki/Coffman%E2%80%93Graham_algorithm to
    // position

    // -100-<s(50)>-50-<i(50)>-50-<sd50>-50-<o50>-100-

    const nodes: {
      [key: string]: GraphNode;
    } = {};
    const links: Array<{ source: string; target: string }> = [];

    this.props.pipeline.solids.forEach((solid, i: number) => {
      const baselineRow = 100;
      const baselineColumn = 50 + i * 1000;
      const sourceColumn = baselineColumn;
      const inputColumn = baselineColumn + 300;
      const solidColumn = inputColumn + 300;
      const outputColumn = solidColumn + 300;

      nodes[solid.name] = {
        id: solid.name,
        x: solidColumn,
        y: baselineRow,
        type: "solid",
        solid
      };

      solid.inputs.forEach((input, i: number) => {
        const inputId = `${solid.name}_input_${input.name}`;
        const inputRow = baselineRow + i * 100;
        nodes[inputId] = {
          id: inputId,
          x: inputColumn,
          y: inputRow,
          type: "input",
          input
        };
        links.push({ source: inputId, target: solid.name });
        if (input.dependsOn) {
          links.push({
            source: `${input.dependsOn.name}_output`,
            target: inputId
          });
        } else {
          input.sources.forEach((source, i: number) => {
            const sourceId = `${inputId}_${source.name}`;
            const sourceRow = inputRow + 30 * i;
            nodes[sourceId] = {
              id: sourceId,
              x: sourceColumn,
              y: sourceRow,
              type: "source",
              source
            };
            links.push({
              source: sourceId,
              target: inputId
            });
          });
        }
      });

      const outputId = `${solid.name}_output`;
      nodes[outputId] = {
        id: outputId,
        x: outputColumn,
        y: baselineRow,
        type: "output",
        output: solid.output
      };

      links.push({ source: solid.name, target: outputId });
    });

    const graph = {
      nodes: Object.keys(nodes).map(id => nodes[id]),
      links: links.map(({ source, target }) => ({
        source: nodes[source],
        target: nodes[target]
      }))
    };

    return (
      <ParentSize>
        {(parent: any) => (
          <SVGContainer width={parent.width} height={parent.height}>
            <BGRect />
            <Graph graph={graph} linkComponent={Link} nodeComponent={Node} />
            <foreignObject>
              <LegendWrapper>
                <LegendOrdinal
                  direction="row"
                  itemDirection="row"
                  shapeMargin="0"
                  labelMargin="0 0 0 4px"
                  itemMargin="0 5px"
                  scale={NodeColorsScale}
                  shape="rect"
                  fill={({ datum }: any) => NodeColorsScale(datum)}
                  labelFormat={(label: string) => `${label.toUpperCase()}`}
                />
              </LegendWrapper>
            </foreignObject>
          </SVGContainer>
        )}
      </ParentSize>
    );
  }
}

function Link({ link }: { link: { source: GraphNode; target: GraphNode } }) {
  return (
    <LinkHorizontalStep
      data={link}
      x={(d: any) => d.x}
      y={(d: any) => d.y}
      stroke="#374469"
      strokeWidth="1"
      fill="none"
    />
  );
}

const Node = ({ node }: { node: GraphNode }) => {
  let color = NodeColorsScale(node.type);
  const width = 200;
  const height = 100;
  return (
    <foreignObject width={width} height={height}>
      <Card elevation={2} style={{ backgroundColor: color }}>
        {node.id}
      </Card>
    </foreignObject>
  );
};

const SVGContainer = styled.svg`
  border-radius: 0;
`;

const BGRect = styled.rect`
  width: 100%;
  height: 100%;
  fill: ${Colors.LIGHT_GRAY5};
`;

const LegendWrapper = styled.div`
  padding: 10px;
  margin: 5px;
  border: 1px solid ${Colors.GRAY1};
  border-radius: 3px;
  width: auto;
  position: absolute;
`;
