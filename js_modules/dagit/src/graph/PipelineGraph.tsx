import {gql} from '@apollo/client';
import {Colors} from '@blueprintjs/core';
import * as React from 'react';
import styled from 'styled-components/macro';

import {ParentSolidNode, SVGLabeledParentRect} from 'src/graph/ParentSolidNode';
import {SVGViewport, DETAIL_ZOOM, SVGViewportInteractor} from 'src/graph/SVGViewport';
import {SolidLinks} from 'src/graph/SolidLinks';
import {
  SolidNode,
  SOLID_NODE_DEFINITION_FRAGMENT,
  SOLID_NODE_INVOCATION_FRAGMENT,
} from 'src/graph/SolidNode';
import {IFullPipelineLayout, IFullSolidLayout, ILayout} from 'src/graph/getFullSolidLayout';
import {Edge, isHighlighted, isSolidHighlighted} from 'src/graph/highlighting';
import {PipelineGraphSolidFragment} from 'src/graph/types/PipelineGraphSolidFragment';
import {SolidNameOrPath} from 'src/solids/SolidNameOrPath';

const NoOp = () => {};

interface IPipelineGraphProps {
  pipelineName: string;
  backgroundColor: string;
  layout: IFullPipelineLayout;
  solids: PipelineGraphSolidFragment[];
  focusSolids: PipelineGraphSolidFragment[];
  parentHandleID?: string;
  parentSolid?: PipelineGraphSolidFragment;
  selectedHandleID?: string;
  selectedSolid?: PipelineGraphSolidFragment;
  highlightedSolids: Array<PipelineGraphSolidFragment>;
  interactor?: SVGViewportInteractor;
  onClickSolid?: (arg: SolidNameOrPath) => void;
  onDoubleClickSolid?: (arg: SolidNameOrPath) => void;
  onEnterCompositeSolid?: (arg: SolidNameOrPath) => void;
  onLeaveCompositeSolid?: () => void;
  onClickBackground?: () => void;
}

interface IPipelineContentsProps extends IPipelineGraphProps {
  minified: boolean;
  layout: IFullPipelineLayout;
}

interface IPipelineContentsState {
  highlighted: Edge[];
}

/**
 * Identifies groups of solids that share a similar `prefix.` and returns
 * an array of bounding boxes and common prefixes. Used to render lightweight
 * outlines around flattened composites.
 */
function computeSolidPrefixBoundingBoxes(layout: IFullPipelineLayout) {
  const groups: {[base: string]: ILayout[]} = {};
  let maxDepth = 0;

  for (const key of Object.keys(layout.solids)) {
    const parts = key.split('.');
    if (parts.length === 1) {
      continue;
    }
    for (let ii = 1; ii < parts.length; ii++) {
      const base = parts.slice(0, ii).join('.');
      groups[base] = groups[base] || [];
      groups[base].push(layout.solids[key].boundingBox);
      maxDepth = Math.max(maxDepth, ii);
    }
  }

  const boxes: (ILayout & {name: string})[] = [];
  for (const base of Object.keys(groups)) {
    const group = groups[base];
    const depth = base.split('.').length;
    const margin = 5 + (maxDepth - depth) * 5;

    if (group.length === 1) {
      continue;
    }
    const x1 = Math.min(...group.map((l) => l.x)) - margin;
    const x2 = Math.max(...group.map((l) => l.x + l.width)) + margin;
    const y1 = Math.min(...group.map((l) => l.y)) - margin;
    const y2 = Math.max(...group.map((l) => l.y + l.height)) + margin;
    boxes.push({name: base, x: x1, y: y1, width: x2 - x1, height: y2 - y1});
  }

  return boxes;
}

export class PipelineGraphContents extends React.PureComponent<
  IPipelineContentsProps,
  IPipelineContentsState
> {
  state: IPipelineContentsState = {
    highlighted: [],
  };

  onHighlightEdges = (highlighted: Edge[]) => {
    this.setState({highlighted});
  };

  render() {
    const {
      layout,
      minified,
      solids,
      focusSolids,
      parentSolid,
      parentHandleID,
      onClickSolid = NoOp,
      onDoubleClickSolid = NoOp,
      onEnterCompositeSolid = NoOp,
      highlightedSolids,
      selectedSolid,
      selectedHandleID,
    } = this.props;

    return (
      <>
        {parentSolid && layout.parent && layout.parent.invocationBoundingBox.width > 0 && (
          <SVGLabeledParentRect
            {...layout.parent.invocationBoundingBox}
            key={`composite-rect-${parentHandleID}`}
            label={parentSolid.name}
            fill={Colors.LIGHT_GRAY5}
            minified={minified}
          />
        )}
        {selectedSolid && layout.solids[selectedSolid.name] && (
          // this rect is hidden beneath the user's selection with a React key so that
          // when they expand the composite solid React sees this component becoming
          // the one above and re-uses the DOM node. This allows us to animate the rect's
          // bounds from the parent layout to the inner layout with no React state.
          <SVGLabeledParentRect
            {...layout.solids[selectedSolid.name].solid}
            key={`composite-rect-${selectedHandleID}`}
            label={''}
            fill={Colors.LIGHT_GRAY5}
            minified={true}
          />
        )}

        {parentSolid && (
          <ParentSolidNode
            onClickSolid={onClickSolid}
            onDoubleClick={(name) => onDoubleClickSolid({name})}
            onHighlightEdges={this.onHighlightEdges}
            highlightedEdges={this.state.highlighted}
            key={`composite-rect-${parentHandleID}-definition`}
            minified={minified}
            solid={parentSolid}
            layout={layout}
          />
        )}
        <SolidLinks
          solids={solids}
          layout={layout}
          opacity={0.2}
          connections={layout.connections}
          onHighlight={this.onHighlightEdges}
        />
        <SolidLinks
          solids={solids}
          layout={layout}
          opacity={0.55}
          onHighlight={this.onHighlightEdges}
          connections={layout.connections.filter(({from, to}) =>
            isHighlighted(this.state.highlighted, {
              a: from.solidName,
              b: to.solidName,
            }),
          )}
        />
        {computeSolidPrefixBoundingBoxes(layout).map((box, idx) => (
          <rect
            key={idx}
            {...box}
            stroke="rgb(230, 219, 238)"
            fill="rgba(230, 219, 238, 0.2)"
            strokeWidth={2}
          />
        ))}
        {solids.map((solid) => (
          <SolidNode
            key={solid.name}
            invocation={solid}
            definition={solid.definition}
            minified={minified}
            onClick={() => onClickSolid({name: solid.name})}
            onDoubleClick={() => onDoubleClickSolid({name: solid.name})}
            onEnterComposite={() => onEnterCompositeSolid({name: solid.name})}
            onHighlightEdges={this.onHighlightEdges}
            layout={layout.solids[solid.name]}
            selected={selectedSolid === solid}
            focused={focusSolids.includes(solid)}
            highlightedEdges={
              isSolidHighlighted(this.state.highlighted, solid.name)
                ? this.state.highlighted
                : EmptyHighlightedArray
            }
            dim={highlightedSolids.length > 0 && highlightedSolids.indexOf(solid) === -1}
          />
        ))}
      </>
    );
  }
}

// This is a specific empty array we pass to represent the common / empty case
// so that SolidNode can use shallow equality comparisons in shouldComponentUpdate.
const EmptyHighlightedArray: never[] = [];

export class PipelineGraph extends React.Component<IPipelineGraphProps> {
  viewportEl: React.RefObject<SVGViewport> = React.createRef();

  resolveSolidPosition = (
    arg: SolidNameOrPath,
    cb: (cx: number, cy: number, layout: IFullSolidLayout) => void,
  ) => {
    const lastName = 'name' in arg ? arg.name : arg.path[arg.path.length - 1];
    const solidLayout = this.props.layout.solids[lastName];
    if (!solidLayout) {
      return;
    }
    const cx = solidLayout.boundingBox.x + solidLayout.boundingBox.width / 2;
    const cy = solidLayout.boundingBox.y + solidLayout.boundingBox.height / 2;
    cb(cx, cy, solidLayout);
  };

  centerSolid = (arg: SolidNameOrPath) => {
    this.resolveSolidPosition(arg, (cx, cy) => {
      const viewportEl = this.viewportEl.current!;
      viewportEl.smoothZoomToSVGCoords(cx, cy, viewportEl.state.scale);
    });
  };

  focusOnSolid = (arg: SolidNameOrPath) => {
    this.resolveSolidPosition(arg, (cx, cy) => {
      this.viewportEl.current!.smoothZoomToSVGCoords(cx, cy, DETAIL_ZOOM);
    });
  };

  closestSolidInDirection = (dir: string): string | undefined => {
    const {layout, selectedSolid} = this.props;
    if (!selectedSolid) {
      return;
    }

    const current = layout.solids[selectedSolid.name];
    const center = (solid: IFullSolidLayout): {x: number; y: number} => ({
      x: solid.boundingBox.x + solid.boundingBox.width / 2,
      y: solid.boundingBox.y + solid.boundingBox.height / 2,
    });

    /* Sort all the solids in the graph based on their attractiveness
    as a jump target. We want the nearest node in the exact same row for left/right,
    and the visually "closest" node above/below for up/down. */
    const score = (solid: IFullSolidLayout): number => {
      const dx = center(solid).x - center(current).x;
      const dy = center(solid).y - center(current).y;

      if (dir === 'left' && dy === 0 && dx < 0) {
        return -dx;
      }
      if (dir === 'right' && dy === 0 && dx > 0) {
        return dx;
      }
      if (dir === 'up' && dy < 0) {
        return -dy + Math.abs(dx) / 5;
      }
      if (dir === 'down' && dy > 0) {
        return dy + Math.abs(dx) / 5;
      }
      return Number.NaN;
    };

    const closest = Object.keys(layout.solids)
      .map((name) => ({name, score: score(layout.solids[name])}))
      .filter((e) => e.name !== selectedSolid.name && !Number.isNaN(e.score))
      .sort((a, b) => b.score - a.score)
      .pop();

    return closest ? closest.name : undefined;
  };

  onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.target && (e.target as HTMLElement).nodeName === 'INPUT') {
      return;
    }

    const dir = {37: 'left', 38: 'up', 39: 'right', 40: 'down'}[e.keyCode];
    if (!dir) {
      return;
    }

    const nextSolid = this.closestSolidInDirection(dir);
    if (nextSolid && this.props.onClickSolid) {
      e.preventDefault();
      e.stopPropagation();
      this.props.onClickSolid({name: nextSolid});
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
      this.viewportEl.current!.cancelAnimations();
      this.viewportEl.current!.autocenter();
    }
    if (prevProps.layout !== this.props.layout) {
      this.viewportEl.current!.autocenter();
    }
    if (prevProps.selectedSolid !== this.props.selectedSolid && this.props.selectedSolid) {
      this.centerSolid(this.props.selectedSolid);
    }
  }

  render() {
    const {
      layout,
      interactor,
      pipelineName,
      backgroundColor,
      onClickBackground,
      onDoubleClickSolid,
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
        {({scale}: any) => (
          <>
            <SVGContainer
              width={layout.width}
              height={layout.height + 200}
              onClick={onClickBackground}
              onDoubleClick={this.unfocus}
            >
              <PipelineGraphContents
                {...this.props}
                layout={layout}
                minified={scale < DETAIL_ZOOM - 0.01}
                onDoubleClickSolid={onDoubleClickSolid || this.focusOnSolid}
              />
            </SVGContainer>
          </>
        )}
      </SVGViewport>
    );
  }
}

export const PIPELINE_GRAPH_SOLID_FRAGMENT = gql`
  fragment PipelineGraphSolidFragment on Solid {
    name
    ...SolidNodeInvocationFragment
    definition {
      name
      ...SolidNodeDefinitionFragment
    }
  }
  ${SOLID_NODE_INVOCATION_FRAGMENT}
  ${SOLID_NODE_DEFINITION_FRAGMENT}
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
