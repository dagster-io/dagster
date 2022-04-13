import {gql} from '@apollo/client';
import {Colors} from '@dagster-io/ui';
import * as React from 'react';
import styled from 'styled-components/macro';

import {OpNameOrPath} from '../ops/OpNameOrPath';

import {OpEdges} from './OpEdges';
import {OpNode, OP_NODE_DEFINITION_FRAGMENT, OP_NODE_INVOCATION_FRAGMENT} from './OpNode';
import {ParentOpNode, SVGLabeledParentRect} from './ParentOpNode';
import {DETAIL_ZOOM, SVGViewport, SVGViewportInteractor} from './SVGViewport';
import {OpGraphLayout, OpLayout, ILayout} from './asyncGraphLayout';
import {Edge, isHighlighted, isOpHighlighted} from './highlighting';
import {OpGraphOpFragment} from './types/OpGraphOpFragment';

const NoOp = () => {};

interface OpGraphProps {
  pipelineName: string;
  layout: OpGraphLayout;
  ops: OpGraphOpFragment[];
  focusOps: OpGraphOpFragment[];
  parentHandleID?: string;
  parentOp?: OpGraphOpFragment;
  selectedHandleID?: string;
  selectedOp?: OpGraphOpFragment;
  highlightedOps: Array<OpGraphOpFragment>;
  interactor?: SVGViewportInteractor;
  onClickOp?: (arg: OpNameOrPath) => void;
  onDoubleClickOp?: (arg: OpNameOrPath) => void;
  onEnterSubgraph?: (arg: OpNameOrPath) => void;
  onLeaveSubgraph?: () => void;
  onClickBackground?: () => void;
}

interface OpGraphContentsProps extends OpGraphProps {
  minified: boolean;
  layout: OpGraphLayout;
  bounds: {top: number; left: number; right: number; bottom: number};
}

/**
 * Identifies groups of ops that share a similar `prefix.` and returns
 * an array of bounding boxes and common prefixes. Used to render lightweight
 * outlines around flattened composites.
 */
function computeOpPrefixBoundingBoxes(layout: OpGraphLayout) {
  const groups: {[base: string]: ILayout[]} = {};
  let maxDepth = 0;

  for (const key of Object.keys(layout.nodes)) {
    const parts = key.split('.');
    if (parts.length === 1) {
      continue;
    }
    for (let ii = 1; ii < parts.length; ii++) {
      const base = parts.slice(0, ii).join('.');
      groups[base] = groups[base] || [];
      groups[base].push(layout.nodes[key].bounds);
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

const OpGraphContents: React.FC<OpGraphContentsProps> = React.memo((props) => {
  const [highlighted, setHighlighted] = React.useState<Edge[]>(() => []);

  const {
    layout,
    minified,
    ops,
    bounds,
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
      {parentOp && layout.parent && layout.parent.invocationBoundingBox.width > 0 && (
        <SVGLabeledParentRect
          {...layout.parent.invocationBoundingBox}
          key={`composite-rect-${parentHandleID}`}
          label=""
          fill={Colors.Yellow50}
          minified={minified}
        />
      )}
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
        color={Colors.KeylineGray}
        edges={layout.edges}
        onHighlight={setHighlighted}
      />
      <OpEdges
        ops={ops}
        layout={layout}
        color={Colors.Blue500}
        onHighlight={setHighlighted}
        edges={layout.edges.filter(({from, to}) =>
          isHighlighted(highlighted, {
            a: from.opName,
            b: to.opName,
          }),
        )}
      />
      {computeOpPrefixBoundingBoxes(layout).map((box, idx) => (
        <rect
          key={idx}
          {...box}
          stroke="rgb(230, 219, 238)"
          fill="rgba(230, 219, 238, 0.2)"
          strokeWidth={2}
        />
      ))}
      <foreignObject width={layout.width} height={layout.height} style={{pointerEvents: 'none'}}>
        {ops
          .filter((op) => {
            const box = layout.nodes[op.name].bounds;
            return (
              box.x + box.width >= bounds.left &&
              box.y + box.height >= bounds.top &&
              box.x < bounds.right &&
              box.y < bounds.bottom
            );
          })
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
              layout={layout.nodes[op.name]}
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
  viewportEl: React.RefObject<SVGViewport> = React.createRef();

  resolveOpPosition = (
    arg: OpNameOrPath,
    cb: (cx: number, cy: number, layout: OpLayout) => void,
  ) => {
    const lastName = 'name' in arg ? arg.name : arg.path[arg.path.length - 1];
    const opLayout = this.props.layout.nodes[lastName];
    if (!opLayout) {
      return;
    }
    const cx = opLayout.bounds.x + opLayout.bounds.width / 2;
    const cy = opLayout.bounds.y + opLayout.bounds.height / 2;
    cb(cx, cy, opLayout);
  };

  centerOp = (arg: OpNameOrPath) => {
    this.resolveOpPosition(arg, (cx, cy) => {
      const viewportEl = this.viewportEl.current!;
      viewportEl.smoothZoomToSVGCoords(cx, cy, viewportEl.state.scale);
    });
  };

  focusOnOp = (arg: OpNameOrPath) => {
    this.resolveOpPosition(arg, (cx, cy) => {
      this.viewportEl.current!.smoothZoomToSVGCoords(cx, cy, DETAIL_ZOOM);
    });
  };

  closestOpInDirection = (dir: string): string | undefined => {
    const {layout, selectedOp} = this.props;
    if (!selectedOp) {
      return;
    }

    const current = layout.nodes[selectedOp.name];
    const center = (op: OpLayout): {x: number; y: number} => ({
      x: op.bounds.x + op.bounds.width / 2,
      y: op.bounds.y + op.bounds.height / 2,
    });

    /* Sort all the ops in the graph based on their attractiveness
    as a jump target. We want the nearest node in the exact same row for left/right,
    and the visually "closest" node above/below for up/down. */
    const score = (op: OpLayout): number => {
      const dx = center(op).x - center(current).x;
      const dy = center(op).y - center(current).y;

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

    const closest = Object.keys(layout.nodes)
      .map((name) => ({name, score: score(layout.nodes[name])}))
      .filter((e) => e.name !== selectedOp.name && !Number.isNaN(e.score))
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

    const nextOp = this.closestOpInDirection(dir);
    if (nextOp && this.props.onClickOp) {
      e.preventDefault();
      e.stopPropagation();
      this.props.onClickOp({name: nextOp});
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

  render() {
    const {layout, interactor, pipelineName, onClickBackground, onDoubleClickOp} = this.props;

    return (
      <SVGViewport
        ref={this.viewportEl}
        key={pipelineName}
        maxZoom={1.2}
        interactor={interactor || SVGViewport.Interactors.PanAndZoom}
        graphWidth={layout.width}
        graphHeight={layout.height}
        onKeyDown={this.onKeyDown}
        onClick={onClickBackground}
        onDoubleClick={this.unfocus}
      >
        {({scale}, bounds) => (
          <SVGContainer width={layout.width} height={layout.height + 200}>
            <OpGraphContents
              {...this.props}
              layout={layout}
              minified={scale < DETAIL_ZOOM - 0.01}
              onDoubleClickOp={onDoubleClickOp || this.focusOnOp}
              bounds={bounds}
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
