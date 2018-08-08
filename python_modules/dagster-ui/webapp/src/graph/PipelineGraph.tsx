import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Card, Colors } from "@blueprintjs/core";
import { LinkHorizontalStep } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import PipelineColorScale from "./PipelineColorScale";
import PipelineLegend from "./PipelineLegend";
import SolidNode from "./SolidNode";
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
          ...SolidNodeFragment
        }
      }

      ${SolidNode.fragments.SolidNodeFragment}
    `
  };

  renderSolids() {
    return this.props.pipeline.solids.map((solid, i) => (
      <g key={i} transform={`translate(${300 + i * 750}, 100) `}>
        <SolidNode
          solid={solid}
          onClick={this.props.onClickSolid}
          selected={this.props.selectedSolid === solid.name}
        />
      </g>
    ));
  }

  render() {
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
            {this.renderSolids()}
          </SVGContainer>
        </PanAndZoomStyled>
      </GraphWrapper>
    );
  }
}

const GraphWrapper = styled.div`
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  user-select: none;
  background-color: ${Colors.LIGHT_GRAY5};
`;

const PanAndZoomStyled = styled(PanAndZoom)`
  width: 100%;
  height: 100%;
`;

const SVGContainer = styled.svg`
  border-radius: 0;
`;

const LegendWrapper = styled.div`
  padding: 10px;
  margin: 5px;
  border: 1px solid ${Colors.GRAY1};
  border-radius: 3px;
  width: auto;
  position: absolute;
`;
