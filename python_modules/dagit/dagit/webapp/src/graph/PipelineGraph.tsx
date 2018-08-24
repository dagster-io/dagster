import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LinkHorizontal as Link } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import SolidNode from "./SolidNode";
import {
  getDagrePipelineLayout,
  IFullPipelineLayout
} from "./getFullSolidLayout";
import { PipelineGraphFragment } from "./types/PipelineGraphFragment";

interface IPipelineGraphProps {
  pipeline: PipelineGraphFragment;
  selectedSolid?: string;
  onClickSolid?: (solidName: string) => void;
}

interface IPipelineGraphState {
  graphWidth: number | null;
  graphHeight: number | null;
}

export default class PipelineGraph extends React.Component<
  IPipelineGraphProps,
  IPipelineGraphState
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

  state = {
    graphWidth: null,
    graphHeight: null
  };

  graphWrapper: React.RefObject<HTMLDivElement> = React.createRef();

  componentDidMount() {
    if (this.graphWrapper.current) {
      this.setState({
        graphWidth: this.graphWrapper.current.clientWidth,
        graphHeight: this.graphWrapper.current.clientHeight
      });
    }
  }

  componentDidUpdate() {
    if (this.graphWrapper.current) {
      if (
        this.state.graphWidth !== this.graphWrapper.current.clientWidth ||
        this.state.graphHeight !== this.graphWrapper.current.clientHeight
      ) {
        this.setState({
          graphWidth: this.graphWrapper.current.clientWidth,
          graphHeight: this.graphWrapper.current.clientHeight
        });
      }
    }
  }

  renderSolids(layout: IFullPipelineLayout) {
    return this.props.pipeline.solids.map(solid => {
      const solidLayout = layout.solids[solid.name];
      return (
        <SolidNode
          key={solid.name}
          solid={solid}
          layout={solidLayout}
          onClick={this.props.onClickSolid}
          selected={this.props.selectedSolid === solid.name}
        />
      );
    });
  }

  renderConnections(layout: IFullPipelineLayout) {
    const connections: Array<{
      from: { solidName: string; outputName: string };
      to: { solidName: string; inputName: string };
    }> = [];

    this.props.pipeline.solids.forEach(solid => {
      solid.inputs.forEach(input => {
        if (input.dependsOn) {
          connections.push({
            from: {
              solidName: input.dependsOn.solid.name,
              outputName: input.dependsOn.name
            },
            to: {
              solidName: solid.name,
              inputName: input.name
            }
          });
        }
      });
    });

    const links = connections.map(
      (
        {
          from: { solidName: outputSolidName, outputName },
          to: { solidName: inputSolidName, inputName }
        },
        i
      ) => (
        <StyledLink
          key={i}
          data={{
            source: layout.solids[outputSolidName].outputs[outputName].port,
            target: layout.solids[inputSolidName].inputs[inputName].port
          }}
          x={(d: { x: number; y: number }) => d.x}
          y={(d: { x: number; y: number }) => d.y}
        />
      )
    );

    return <g>{links}</g>;
  }

  render() {
    const layout = getDagrePipelineLayout(this.props.pipeline);

    let minScale;
    const { graphWidth, graphHeight } = this.state;
    if (graphWidth !== null && graphHeight !== null) {
      if (graphWidth > graphHeight) {
        minScale = graphWidth / (layout.width + 200);
      } else {
        minScale = graphHeight / (layout.height - 300);
      }
    } else {
      minScale = 0.1;
    }

    return (
      <GraphWrapper innerRef={this.graphWrapper}>
        <PanAndZoomStyled
          width={layout.width}
          height={layout.height + 300}
          renderOnChange={true}
          minScale={minScale}
          maxScale={1}
          minX={0.5}
        >
          <SVGContainer
            width={layout.width}
            height={layout.height + 300}
            onMouseDown={evt => evt.preventDefault()}
          >
            {this.renderConnections(layout)}
            {this.renderSolids(layout)}
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

const StyledLink = styled(Link)`
  stroke-width: 2;
  stroke: ${Colors.BLACK}
  strokeOpacity: 0.6;
  fill: none;
`;
