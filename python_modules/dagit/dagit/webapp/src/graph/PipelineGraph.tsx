import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LinkVertical as Link } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import SolidNode from "./SolidNode";
import { getDagrePipelineLayout, IPoint } from "./getFullSolidLayout";
import { PipelineGraphFragment } from "./types/PipelineGraphFragment";

interface IPipelineGraphProps {
  pipeline: PipelineGraphFragment;
  selectedSolid?: string;
  onClickSolid?: (solidName: string) => void;
}

export default class PipelineGraph extends React.Component<
  IPipelineGraphProps,
  {}
> {
  static fragments = {
    PipelineGraphFragment: gql`
      fragment PipelineGraphFragment on Pipeline {
        name
        solids {
          ...SolidNodeFragment
        }
      }

      ${SolidNode.fragments.SolidNodeFragment}
    `
  };

  render() {
    const { pipeline, onClickSolid, selectedSolid } = this.props;
    const layout = getDagrePipelineLayout(this.props.pipeline);

    return (
      <GraphWrapper>
        <PanAndZoomStyled
          key={pipeline.name}
          graphWidth={layout.width}
          graphHeight={layout.height}
        >
          <SVGContainer
            width={layout.width}
            height={layout.height}
            onMouseDown={evt => evt.preventDefault()}
          >
            {pipeline.solids.map(solid => (
              <SolidNode
                key={solid.name}
                solid={solid}
                onClick={onClickSolid}
                layout={layout.solids[solid.name]}
                selected={selectedSolid === solid.name}
              />
            ))}
            <g>
              {layout.connections.map(({ from, to }, i) => (
                <StyledLink
                  key={i}
                  x={(d: IPoint) => d.x}
                  y={(d: IPoint) => d.y}
                  data={{
                    // can also use from.point for the "Dagre" closest point on node
                    source:
                      layout.solids[from.solidName].outputs[from.edgeName].port,
                    target: layout.solids[to.solidName].inputs[to.edgeName].port
                  }}
                />
              ))}
            </g>
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
