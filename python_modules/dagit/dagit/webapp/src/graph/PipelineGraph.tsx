import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LinkVertical as Link } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import SolidNode from "./SolidNode";
import { IPoint, IFullPipelineLayout } from "./getFullSolidLayout";
import {
  PipelineGraphFragment,
  PipelineGraphFragment_solids
} from "./types/PipelineGraphFragment";

interface IPipelineGraphProps {
  pipeline: PipelineGraphFragment;
  layout: IFullPipelineLayout;
  selectedSolid?: PipelineGraphFragment_solids;
  highlightedSolids: Array<PipelineGraphFragment_solids>;
  onClickSolid?: (solidName: string) => void;
  onDoubleClickSolid?: (solidName: string) => void;
  onClickBackground?: () => void;
}

interface IPipelineContentsProps extends IPipelineGraphProps {
  minified: boolean;
  layout: IFullPipelineLayout;
}

class PipelineGraphContents extends React.PureComponent<
  IPipelineContentsProps
> {
  render() {
    const {
      layout,
      minified,
      pipeline,
      onClickSolid,
      onDoubleClickSolid,
      highlightedSolids,
      selectedSolid
    } = this.props;

    return (
      <g>
        <g style={{ opacity: 0.2 }}>
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
        {pipeline.solids.map(solid => (
          <SolidNode
            key={solid.name}
            solid={solid}
            minified={minified}
            onClick={onClickSolid}
            onDoubleClick={onDoubleClickSolid}
            layout={layout.solids[solid.name]}
            selected={selectedSolid === solid}
            dim={
              highlightedSolids.length > 0 &&
              highlightedSolids.indexOf(solid) == -1
            }
          />
        ))}
      </g>
    );
  }
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

  viewportEl: React.RefObject<PanAndZoom> = React.createRef();

  focusOnSolid = (solidName: string) => {
    const solidLayout = this.props.layout.solids[solidName];
    if (!solidLayout) {
      return;
    }
    const cx = solidLayout.boundingBox.x + solidLayout.boundingBox.width / 2;
    const cy = solidLayout.boundingBox.y + solidLayout.boundingBox.height / 2;
    this.viewportEl.current!.smoothZoomToSVGCoords(cx, cy, 1);
  };

  unfocus = () => {
    this.viewportEl.current!.autocenter(true);
  };

  render() {
    const { layout, pipeline, onClickBackground } = this.props;

    return (
      <PanAndZoom
        key={this.props.pipeline.name}
        ref={this.viewportEl}
        graphWidth={layout.width}
        graphHeight={layout.height}
      >
        {({ scale }: any) => (
          <SVGContainer
            width={layout.width}
            height={layout.height}
            onMouseDown={evt => evt.preventDefault()}
            onClick={onClickBackground}
            onDoubleClick={this.unfocus}
          >
            <PipelineGraphContents
              layout={layout}
              minified={scale < 0.4}
              onDoubleClickSolid={this.focusOnSolid}
              {...this.props}
            />
          </SVGContainer>
        )}
      </PanAndZoom>
    );
  }
}

const SVGContainer = styled.svg`
  border-radius: 0;
`;

const StyledLink = styled(Link)`
  stroke-width: 6;
  stroke: ${Colors.BLACK}
  fill: none;
`;
