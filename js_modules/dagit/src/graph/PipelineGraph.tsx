import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import { LinkVertical as Link } from "@vx/shape";
import SVGViewport, { SVGViewportInteractor } from "./SVGViewport";
import { SVGLabeledRect } from "./SVGComponents";
import SolidNode from "./SolidNode";
import {
  ILayoutConnection,
  IFullPipelineLayout,
  IFullSolidLayout
} from "./getFullSolidLayout";
import { PipelineGraphSolidFragment } from "./types/PipelineGraphSolidFragment";

const NoOp = () => {};

interface IPipelineGraphProps {
  pipelineName: string;
  backgroundColor: string;
  layout: IFullPipelineLayout;
  solids: PipelineGraphSolidFragment[];
  parentSolid?: PipelineGraphSolidFragment;
  selectedSolid?: PipelineGraphSolidFragment;
  highlightedSolids: Array<PipelineGraphSolidFragment>;
  interactor?: SVGViewportInteractor;
  onClickSolid?: (solidName: string) => void;
  onDoubleClickSolid?: (solidName: string) => void;
  onExpandCompositeSolid?: (solidName: string) => void;
  onClickBackground?: () => void;
}

interface IPipelineContentsProps extends IPipelineGraphProps {
  minified: boolean;
  layout: IFullPipelineLayout;
}

type IConnHighlight = { a: string; b: string };
interface IPipelineContentsState {
  highlightedConnections: IConnHighlight[];
}

class PipelineGraphContents extends React.PureComponent<
  IPipelineContentsProps,
  IPipelineContentsState
> {
  state: IPipelineContentsState = {
    highlightedConnections: []
  };

  onHighlightConnections = (connections: IConnHighlight[]) => {
    this.setState({ highlightedConnections: connections });
  };

  render() {
    const {
      layout,
      minified,
      solids,
      parentSolid,
      onClickSolid = NoOp,
      onDoubleClickSolid = NoOp,
      highlightedSolids,
      selectedSolid
    } = this.props;

    const { highlightedConnections } = this.state;

    const isHighlighted = (c: ILayoutConnection) => {
      const from = c.from.solidName;
      const to = c.to.solidName;
      return highlightedConnections.find(
        h => (h.a === from && h.b === to) || (h.b === from && h.a === to)
      );
    };

    return (
      <g>
        {parentSolid && (
          <SVGLabeledRect
            x={1}
            y={1}
            width={layout.width - 1}
            height={layout.height - 1}
            label={parentSolid.name}
            fill={Colors.LIGHT_GRAY5}
            minified={minified}
          />
        )}
        <SolidLinks
          layout={layout}
          opacity={0.2}
          connections={layout.connections}
          onHighlight={this.onHighlightConnections}
        />
        <SolidLinks
          layout={layout}
          opacity={0.55}
          connections={layout.connections.filter(c => isHighlighted(c))}
          onHighlight={this.onHighlightConnections}
        />
        {solids.map(solid => (
          <SolidNode
            key={solid.name}
            solid={solid}
            parentSolid={parentSolid}
            minified={minified}
            onClick={onClickSolid}
            onDoubleClick={onDoubleClickSolid}
            onHighlightConnections={this.onHighlightConnections}
            layout={layout.solids[solid.name]}
            selected={selectedSolid === solid}
            highlightedConnections={
              highlightedConnections.some(
                c => c.a === solid.name || c.b === solid.name
              )
                ? highlightedConnections
                : []
            }
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
  IPipelineGraphProps
> {
  static fragments = {
    PipelineGraphSolidFragment: gql`
      fragment PipelineGraphSolidFragment on Solid {
        name
        ...SolidNodeFragment
      }

      ${SolidNode.fragments.SolidNodeFragment}
    `
  };

  viewportEl: React.RefObject<SVGViewport> = React.createRef();

  focusOnSolid = (solidName: string) => {
    const { layout, solids, onExpandCompositeSolid } = this.props;

    const solidLayout = layout.solids[solidName];
    if (!solidLayout) {
      return;
    }
    const cx = solidLayout.boundingBox.x + solidLayout.boundingBox.width / 2;
    const cy = solidLayout.boundingBox.y + solidLayout.boundingBox.height / 2;

    const solid = solids.find(s => s.name === solidName);
    const started = this.viewportEl.current!.smoothZoomToSVGCoords(cx, cy, 1);
    if (
      !started &&
      onExpandCompositeSolid &&
      solid!.definition.__typename === "CompositeSolidDefinition"
    ) {
      onExpandCompositeSolid(solidName);
    }
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
    const {
      layout,
      interactor,
      pipelineName,
      parentSolid,
      backgroundColor,
      onClickBackground,
      onDoubleClickSolid
    } = this.props;

    return (
      <SVGViewport
        ref={this.viewportEl}
        key={pipelineName}
        interactor={interactor || SVGViewport.Interactors.PanAndZoom}
        backgroundColor={backgroundColor}
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
              onDoubleClickSolid={onDoubleClickSolid || this.focusOnSolid}
              {...this.props}
            />
          </SVGContainer>
        )}
      </SVGViewport>
    );
  }
}

const SolidLinks = React.memo(
  (props: {
    opacity: number;
    layout: IFullPipelineLayout;
    connections: ILayoutConnection[];
    onHighlight: (arr: IConnHighlight[]) => void;
  }) => {
    const solids = props.layout.solids;

    return (
      <g style={{ opacity: props.opacity }}>
        {props.connections.map(({ from, to }, i) => (
          <g
            key={i}
            onMouseLeave={() => props.onHighlight([])}
            onMouseEnter={() =>
              props.onHighlight([{ a: from.solidName, b: to.solidName }])
            }
          >
            <StyledLink
              data={{
                // can also use from.point for the "Dagre" closest point on node
                source: solids[from.solidName].outputs[from.edgeName].port,
                target: solids[to.solidName].inputs[to.edgeName].port
              }}
            >
              <title>{`${from.solidName} - ${to.solidName}`}</title>
            </StyledLink>
          </g>
        ))}
      </g>
    );
  }
);

SolidLinks.displayName = "SolidLinks";

const SVGContainer = styled.svg`
  border-radius: 0;
`;

const StyledLink = styled(Link)`
  stroke-width: 6;
  stroke: ${Colors.BLACK}
  fill: none;
`;
