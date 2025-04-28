import {Colors} from '@dagster-io/ui-components';
import * as React from 'react';
import styled from 'styled-components';

import {OpEdges} from './OpEdges';
import {OP_NODE_DEFINITION_FRAGMENT, OP_NODE_INVOCATION_FRAGMENT, OpNode} from './OpNode';
import {ParentOpNode} from './ParentOpNode';
import {DEFAULT_MAX_ZOOM, DETAIL_ZOOM} from './SVGConsts';
import {SVGViewport, SVGViewportRef} from './SVGViewport';
import {OpGraphLayout} from './asyncGraphLayout';
import {
  Edge,
  closestNodeInDirection,
  computeNodeKeyPrefixBoundingBoxes,
  isHighlighted,
  isNodeOffscreen,
  isOpHighlighted,
} from './common';
import {gql} from '../apollo-client';
import {OpGraphOpFragment} from './types/OpGraph.types';
import {OpNameOrPath} from '../ops/OpNameOrPath';

const NoOp = () => {};

interface OpGraphProps {
  jobName: string;
  layout: OpGraphLayout;
  ops: OpGraphOpFragment[];
  focusOps: OpGraphOpFragment[];
  parentHandleID?: string;
  parentOp?: OpGraphOpFragment;
  selectedHandleID?: string;
  selectedOp?: OpGraphOpFragment;
  highlightedOps: Array<OpGraphOpFragment>;
  onClickOp?: (arg: OpNameOrPath) => void;
  onDoubleClickOp?: (arg: OpNameOrPath) => void;
  onEnterSubgraph?: (arg: OpNameOrPath) => void;
  onLeaveSubgraph?: () => void;
  onClickBackground?: () => void;
}

interface OpGraphContentsProps extends OpGraphProps {
  minified: boolean;
  layout: OpGraphLayout;
  viewportRect: {top: number; left: number; right: number; bottom: number};
}

const OpGraphContents = React.memo((props: OpGraphContentsProps) => {
  const [highlighted, setHighlighted] = React.useState<Edge[]>(() => []);

  const {
    layout,
    minified,
    ops,
    viewportRect,
    focusOps,
    parentOp,
    parentHandleID,
    onClickOp = NoOp,
    onDoubleClickOp = NoOp,
    onEnterSubgraph = NoOp,
    highlightedOps,
    selectedOp,
  } = props;

  return (
    <>
      {parentOp && (
        <ParentOpNode
          onClickOp={onClickOp}
          onDoubleClick={(name) => onDoubleClickOp({name})}
          onHighlightEdges={setHighlighted}
          highlightedEdges={highlighted}
          key={`composite-rect-${parentHandleID}-definition`}
          minified={minified}
          op={parentOp}
          layout={layout}
        />
      )}
      <OpEdges
        ops={ops}
        layout={layout}
        color={Colors.lineageEdge()}
        edges={layout.edges}
        onHighlight={setHighlighted}
      />
      <OpEdges
        ops={ops}
        layout={layout}
        color={Colors.accentBlue()}
        onHighlight={setHighlighted}
        edges={layout.edges.filter(({from, to}) =>
          isHighlighted(highlighted, {a: from.opName, b: to.opName}),
        )}
      />
      {computeNodeKeyPrefixBoundingBoxes(layout).map((box, idx) => (
        <rect
          key={idx}
          {...box}
          stroke={Colors.backgroundBlue()}
          fill={Colors.backgroundBlueHover()}
          strokeWidth={2}
        />
      ))}
      <foreignObject width={layout.width} height={layout.height} style={{pointerEvents: 'none'}}>
        {ops
          .filter((op) => !isNodeOffscreen(layout.nodes[op.name]!.bounds, viewportRect))
          .map((op) => (
            <OpNode
              key={op.name}
              invocation={op}
              definition={op.definition}
              minified={minified}
              onClick={() => onClickOp({name: op.name})}
              onDoubleClick={() => onDoubleClickOp({name: op.name})}
              onEnterComposite={() => onEnterSubgraph({name: op.name})}
              onHighlightEdges={setHighlighted}
              layout={layout.nodes[op.name]!}
              selected={selectedOp === op}
              focused={focusOps.includes(op)}
              highlightedEdges={
                isOpHighlighted(highlighted, op.name) ? highlighted : EmptyHighlightedArray
              }
              dim={highlightedOps.length > 0 && highlightedOps.indexOf(op) === -1}
            />
          ))}
      </foreignObject>
    </>
  );
});

OpGraphContents.displayName = 'OpGraphContents';

// This is a specific empty array we pass to represent the common / empty case
// so that OpNode can use shallow equality comparisons in shouldComponentUpdate.
const EmptyHighlightedArray: never[] = [];

export class OpGraph extends React.Component<OpGraphProps> {
  viewportEl: React.RefObject<SVGViewportRef> = React.createRef();

  argToOpLayout = (arg: OpNameOrPath) => {
    const lastName = 'name' in arg ? arg.name : arg.path[arg.path.length - 1]!;
    return this.props.layout.nodes[lastName];
  };

  centerOp = (arg: OpNameOrPath) => {
    const opLayout = this.argToOpLayout(arg);
    if (opLayout && this.viewportEl.current) {
      this.viewportEl.current.zoomToSVGBox(opLayout.bounds, true);
    }
  };

  focusOnOp = (arg: OpNameOrPath) => {
    const opLayout = this.argToOpLayout(arg);
    if (opLayout && this.viewportEl.current) {
      this.viewportEl.current?.zoomToSVGBox(opLayout.bounds, true, DETAIL_ZOOM);
    }
  };

  unfocus = (e: React.MouseEvent<any>) => {
    this.viewportEl.current!.autocenter(true);
    e.stopPropagation();
  };

  componentDidUpdate(prevProps: OpGraphProps) {
    if (prevProps.parentOp !== this.props.parentOp) {
      this.viewportEl.current!.cancelAnimations();
      this.viewportEl.current!.autocenter();
    }
    if (prevProps.layout !== this.props.layout) {
      this.viewportEl.current!.autocenter();
    }
    if (prevProps.selectedOp !== this.props.selectedOp && this.props.selectedOp) {
      this.centerOp(this.props.selectedOp);
    }
  }

  onArrowKeyDown = (_e: React.KeyboardEvent<any>, dir: 'left' | 'right' | 'up' | 'down') => {
    const nextOp = closestNodeInDirection(this.props.layout, this.props.selectedOp?.name, dir);
    if (nextOp && this.props.onClickOp) {
      this.props.onClickOp({name: nextOp});
    }
  };

  render() {
    const {layout, jobName, onClickBackground, onDoubleClickOp} = this.props;

    return (
      <SVGViewport
        ref={this.viewportEl}
        key={jobName}
        maxZoom={DEFAULT_MAX_ZOOM}
        defaultZoom="zoom-to-fit"
        graphWidth={layout.width}
        graphHeight={layout.height}
        onClick={onClickBackground}
        onDoubleClick={this.unfocus}
        onArrowKeyDown={this.onArrowKeyDown}
      >
        {({scale}, viewportRect) => (
          <SVGContainer width={layout.width} height={layout.height + 200}>
            <OpGraphContents
              {...this.props}
              layout={layout}
              minified={scale < DETAIL_ZOOM - 0.01}
              onDoubleClickOp={onDoubleClickOp || this.focusOnOp}
              viewportRect={viewportRect}
            />
          </SVGContainer>
        )}
      </SVGViewport>
    );
  }
}

export const OP_GRAPH_OP_FRAGMENT = gql`
  fragment OpGraphOpFragment on Solid {
    name
    ...OpNodeInvocationFragment
    definition {
      name
      ...OpNodeDefinitionFragment
    }
  }

  ${OP_NODE_INVOCATION_FRAGMENT}
  ${OP_NODE_DEFINITION_FRAGMENT}
`;

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
