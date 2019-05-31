import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { Colors } from "@blueprintjs/core";
import SVGViewport, { SVGViewportInteractor } from "./SVGViewport";
import { SVGLabeledRect } from "./SVGComponents";
import SolidNode from "./SolidNode";
import {
  ILayoutConnection,
  IFullPipelineLayout,
  IFullSolidLayout
} from "./getFullSolidLayout";
import { PipelineGraphSolidFragment } from "./types/PipelineGraphSolidFragment";
import { SolidLinks, IConnHighlight } from "./SolidLinks";

const NoOp = () => {};

interface IPipelineGraphProps {
  pipelineName: string;
  backgroundColor: string;
  layout: IFullPipelineLayout;
  solids: PipelineGraphSolidFragment[];
  parentHandleID?: string;
  parentSolid?: PipelineGraphSolidFragment;
  selectedHandleID?: string;
  selectedSolid?: PipelineGraphSolidFragment;
  highlightedSolids: Array<PipelineGraphSolidFragment>;
  interactor?: SVGViewportInteractor;
  onClickSolid?: (solidName: string) => void;
  onDoubleClickSolid?: (solidName: string) => void;
  onEnterCompositeSolid?: (solidName: string) => void;
  onLeaveCompositeSolid?: () => void;
  onClickBackground?: () => void;
}

interface IPipelineContentsProps extends IPipelineGraphProps {
  minified: boolean;
  layout: IFullPipelineLayout;
}

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
      parentHandleID,
      onClickSolid = NoOp,
      onDoubleClickSolid = NoOp,
      onEnterCompositeSolid = NoOp,
      highlightedSolids,
      selectedSolid,
      selectedHandleID
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
          <SVGLabeledCompositeRect
            x={1}
            y={1}
            key={`composite-rect-${parentHandleID}`}
            width={layout.width - 1}
            height={layout.height - 1}
            label={parentSolid ? parentSolid.name : ""}
            fill={Colors.LIGHT_GRAY5}
            minified={minified}
          />
        )}
        {selectedSolid && (
          // this rect is hidden beneath the user's selection with a React key so that
          // when they expand the composite solid React sees this component becoming
          // the one above and re-uses the DOM node. This allows us to animate the rect's
          // bounds from the parent layout to the inner layout with no React state.
          <SVGLabeledCompositeRect
            {...layout.solids[selectedSolid.name].solid}
            key={`composite-rect-${selectedHandleID}`}
            label={""}
            fill={Colors.LIGHT_GRAY5}
            minified={true}
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
            onEnterComposite={onEnterCompositeSolid}
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

  unfocus = (e: React.MouseEvent<any>) => {
    this.viewportEl.current!.autocenter(true);
    e.stopPropagation();
  };

  unfocusOutsideContainer = (e: React.MouseEvent<any>) => {
    if (this.props.parentSolid && this.props.onLeaveCompositeSolid) {
      this.props.onLeaveCompositeSolid();
    } else {
      this.unfocus(e);
    }
  };

  componentDidUpdate(prevProps: IPipelineGraphProps) {
    if (prevProps.parentSolid !== this.props.parentSolid) {
      this.viewportEl.current!.autocenter();
    }
  }

  render() {
    const {
      layout,
      interactor,
      pipelineName,
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
        onDoubleClick={this.unfocusOutsideContainer}
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

const SVGContainer = styled.svg`
  border-radius: 0;
`;

const SVGLabeledCompositeRect = styled(SVGLabeledRect)`
  transition: x 250ms ease-out, y 250ms ease-out, width 250ms ease-out,
    height 250ms ease-out;
`;
