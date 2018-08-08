import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Card, Colors } from "@blueprintjs/core";
import { Graph } from "@vx/network";
import { LinkHorizontalStep } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import PipelineColorScale from "./PipelineColorScale";
import PipelineLegend from "./PipelineLegend";
import {
  PipelineGraphFragment,
  PipelineGraphFragment_solids,
  PipelineGraphFragment_solids_inputs,
  PipelineGraphFragment_solids_output,
  PipelineGraphFragment_solids_inputs_sources
} from "./types/PipelineGraphFragment";

interface IPipelineGraphProps {
  pipeline: PipelineGraphFragment;
  selectedSolid?: string;
  onClickSolid?: (solidName: string) => void;
}

interface IGraphNode {
  id: string;
  name: string;
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
            type {
              name
            }
            sources {
              name: sourceType
            }
            dependsOn {
              name
            }
          }
          output {
            type {
              name
            }
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
      const baselineColumn = 100 + i * 750;
      const sourceColumn = baselineColumn;
      const inputColumn = baselineColumn + 250;
      const solidColumn = inputColumn + 250;
      const outputColumn = solidColumn + 250;

      nodes[solid.name] = {
        id: solid.name,
        x: solidColumn,
        y: baselineRow,
        type: "solid",
        name: solid.name,
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
          name: `${input.name} (${input.type.name})`,
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
            const sourceRow = inputRow + 80 * i;
            nodes[sourceId] = {
              id: sourceId,
              x: sourceColumn,
              y: sourceRow,
              type: "source",
              name: source.name,
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
        name: `output (${solid.output.type.name})`,
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

    const requiredWidth = this.props.pipeline.solids.length * 900;

    return (
      <GraphWrapper>
        <LegendWrapper>
          <PipelineLegend />
        </LegendWrapper>
        <PanAndZoomStyled
          width={requiredWidth}
          height={1000}
          renderOnChange={true}
          scaleFactor={1.1}
        >
          <SVGContainer width={requiredWidth} height={1000}>
            <Graph graph={graph} linkComponent={Link} nodeComponent={Node} />
            <foreignObject />
          </SVGContainer>
        </PanAndZoomStyled>
      </GraphWrapper>
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
      percent={0.6}
    />
  );
}

const Node = ({ node }: { node: GraphNode }) => {
  let color = PipelineColorScale(node.type);
  const width = 200;
  const height = 100;
  return (
    <foreignObject width={width} height={height}>
      <Card
        elevation={2}
        style={{
          backgroundColor: color,
          top: -25,
          left: -75,
          position: "relative"
        }}
      >
        {node.name}
      </Card>
    </foreignObject>
  );
};

const PanAndZoomStyled = styled(PanAndZoom)`
  width: 100%;
  height: 100%;
`;

const SVGContainer = styled.svg`
  border-radius: 0;
`;

const GraphWrapper = styled.div`
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  user-select: none;
  background-color: ${Colors.LIGHT_GRAY5};
`;

const LegendWrapper = styled.div`
  padding: 10px;
  margin: 5px;
  border: 1px solid ${Colors.GRAY1};
  border-radius: 3px;
  width: auto;
  position: absolute;
`;
