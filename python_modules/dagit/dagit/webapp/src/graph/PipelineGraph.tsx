import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LinkVertical as Link } from "@vx/shape";
import PanAndZoom from "./PanAndZoom";
import SolidNode from "./SolidNode";
import {
  IPoint,
  ILayoutConnection,
  IFullPipelineLayout,
  IFullSolidLayout
} from "./getFullSolidLayout";
import { PipelineGraphFragment } from "./types/PipelineGraphFragment";
import { PipelineGraphSolidFragment } from "./types/PipelineGraphSolidFragment";

interface IPipelineGraphProps {
  pipeline: PipelineGraphFragment;
  layout: IFullPipelineLayout;
  selectedSolid?: PipelineGraphSolidFragment;
  highlightedSolids: Array<PipelineGraphSolidFragment>;
  onClickSolid?: (solidName: string) => void;
  onDoubleClickSolid?: (solidName: string) => void;
  onClickBackground?: () => void;
}

interface IPipelineContentsProps extends IPipelineGraphProps {
  minified: boolean;
  layout: IFullPipelineLayout;
}

interface IPipelineContentsState {
  highlightedConnections: { a: string; b: string }[];
}

class PipelineGraphContents extends React.PureComponent<
  IPipelineContentsProps,
  IPipelineContentsState
> {
  state: IPipelineContentsState = {
    highlightedConnections: []
  };

  renderConnections(connections: ILayoutConnection[]) {
    const solids = this.props.layout.solids;

    return connections.map(({ from, to }, i) => (
      <StyledLink
        key={i}
        onClick={() => console.log({ from, to })}
        x={(d: IPoint) => d.x}
        y={(d: IPoint) => d.y}
        data={{
          // can also use from.point for the "Dagre" closest point on node
          source: solids[from.solidName].outputs[from.edgeName].port,
          target: solids[to.solidName].inputs[to.edgeName].port
        }}
      />
    ));
  }

  render() {
    const {
      layout,
      minified,
      pipeline,
      onClickSolid = () => {},
      onDoubleClickSolid = () => {},
      highlightedSolids,
      selectedSolid
    } = this.props;

    const isHighlighted = (c: ILayoutConnection) => {
      const from = c.from.solidName;
      const to = c.to.solidName;
      return this.state.highlightedConnections.find(
        h => (h.a === from && h.b === to) || (h.b === from && h.a === to)
      );
    };

    return (
      <g>
        <g style={{ opacity: 0.2 }}>
          {this.renderConnections(
            layout.connections.filter(c => !isHighlighted(c))
          )}
        </g>
        <g style={{ opacity: 0.75 }}>
          {this.renderConnections(
            layout.connections.filter(c => isHighlighted(c))
          )}
        </g>
        {pipeline.solids.map(solid => (
          <SolidNode
            key={solid.name}
            solid={solid}
            minified={minified}
            onClick={onClickSolid}
            onDoubleClick={onDoubleClickSolid}
            onHighlightConnections={connections =>
              this.setState({ highlightedConnections: connections })
            }
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
    `,
    PipelineGraphSolidFragment: gql`
      fragment PipelineGraphSolidFragment on Solid {
        name
        ...SolidNodeFragment
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

    /* Sort all the solids in the graph based on their attractiveness
    as a jump target. We want the nearest node in the exact same row for left/right,
    and the visually "closest" node above/below for up/down. */
    const score = (solid: IFullSolidLayout): number => {
      const dx = center(solid).x - center(current).x;
      const dy = center(solid).y - center(current).y;

      if (dir === "left" && dy === 0 && dx < 0) {
        return -dx;
      }
      if (dir === "right" && dy === 0 && dx > 0) {
        return dx;
      }
      if (dir === "up" && dy < 0) {
        return -dy + Math.abs(dx) / 5;
      }
      if (dir === "down" && dy > 0) {
        return dy + Math.abs(dx) / 5;
      }
      return Number.NaN;
    };

    let closest = Object.keys(layout.solids)
      .map(name => ({ name, score: score(layout.solids[name]) }))
      .filter(e => e.name !== selectedSolid.name && !Number.isNaN(e.score))
      .sort((a, b) => b.score - a.score)
      .pop();

    return closest ? closest.name : undefined;
  };

  onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.target && (e.target as HTMLElement).nodeName === "INPUT") return;

    const dir = { 37: "left", 38: "up", 39: "right", 40: "down" }[e.keyCode];
    if (!dir) return;

    const nextSolid = this.closestSolidInDirection(dir);
    if (nextSolid && this.props.onClickSolid) {
      e.preventDefault();
      e.stopPropagation();
      this.props.onClickSolid(nextSolid);
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
