import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LinkVertical as Link } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import SolidNode from "./SolidNode";
import {
  IPoint,
  IFullPipelineLayout,
  IFullSolidLayout
} from "./getFullSolidLayout";
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

  closestSolidInDirection = (dir: string): string | undefined => {
    const { layout, selectedSolid } = this.props;
    if (!selectedSolid) return;

    const current = layout.solids[selectedSolid.name];
    const center = (solid: IFullSolidLayout): { x: number; y: number } => ({
      x: solid.boundingBox.x + solid.boundingBox.width / 2,
      y: solid.boundingBox.y + solid.boundingBox.height / 2
    });
    const score = (solid: IFullSolidLayout): number => {
      const dx = center(current).x - center(solid).x;
      const dy = center(current).y - center(solid).y;
      if (dir === "left") {
        return dy === 0 && dx > 0 ? dx : 100000;
      }
      if (dir === "right") {
        return dy === 0 && dx < 0 ? -dx : 100000;
      }
      if (dir === "up" && dy < 0) {
        return -dy + Math.abs(dx) / 5;
      }
      if (dir === "down" && dy > 0) {
        return dy + Math.abs(dx) / 5;
      }
      return 100000;
    };

    const closest = Object.keys(layout.solids)
      .map(name => ({ name: name, score: score(layout.solids[name]) }))
      .filter(({ name }) => name != selectedSolid.name)
      .sort((a, b) => b.score - a.score)
      .pop();

    return closest ? closest.name : undefined;
  };

  onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.target && (e.target as HTMLElement).nodeName === "INPUT") return;

    let next: string | undefined;
    if (e.keyCode === 37) {
      next = this.closestSolidInDirection("left");
    } else if (e.keyCode === 39) {
      next = this.closestSolidInDirection("right");
    } else if (e.keyCode === 38) {
      next = this.closestSolidInDirection("down");
    } else if (e.keyCode === 40) {
      next = this.closestSolidInDirection("up");
    }
    if (next && this.props.onClickSolid) {
      e.preventDefault();
      e.stopPropagation();
      this.props.onClickSolid(next);
    }
  };

  unfocus = () => {
    this.viewportEl.current!.autocenter(true);
  };

  render() {
    const { layout, onClickBackground } = this.props;

    return (
      <PanAndZoom
        key={this.props.pipeline.name}
        ref={this.viewportEl}
        graphWidth={layout.width}
        graphHeight={layout.height}
        onKeyDown={this.onKeyDown}
      >
        {({ scale }: any) => (
          <SVGContainer
            width={layout.width}
            height={layout.height}
            onClick={onClickBackground}
            onDoubleClick={this.unfocus}
          >
            <PipelineGraphContents
              layout={layout}
              minified={scale < 0.99}
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
