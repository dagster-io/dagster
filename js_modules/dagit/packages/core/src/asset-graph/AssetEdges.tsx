import {Colors} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {IPoint, isPointWayOffscreen} from '../graph/common';

import {ForeignNode} from './ForeignNode';
import {buildSVGPath} from './Utils';
import {AssetGraphLayout, AssetLayoutEdge, getForeignNodeDimensions} from './layout';

export const AssetConnectedEdges: React.FC<{
  edges: AssetLayoutEdge[];
  highlighted: string | null;
}> = ({edges, highlighted}) => {
  // Note: we render the highlighted edges twice, but it's so that the first item with
  // all the edges in it can remain memoized.
  return (
    <React.Fragment key="connected">
      <AssetEdges color={Colors.KeylineGray} edges={edges} />
      <AssetEdges
        color={Colors.Blue500}
        edges={edges.filter(({fromId, toId}) => highlighted === fromId || highlighted === toId)}
      />
    </React.Fragment>
  );
};

// No use memoizing this because disconnected edges depend on `viewport`
export const AssetDisconnectedEdges: React.FC<{
  layout: AssetGraphLayout;
  highlighted: string | null;
  setHighlighted: (h: string | null) => void;
  onGoToPoint: (p: IPoint) => void;
  viewport: {
    top: number;
    left: number;
    bottom: number;
    right: number;
  };
}> = ({layout, viewport, highlighted, setHighlighted, onGoToPoint}) => {
  const placedLabels: {[otherId: string]: IPoint} = {};
  const offsetIncrements: {[anchorId: string]: number} = {};
  const nodes: React.ReactNode[] = [];
  const edges: React.ReactNode[] = [];

  for (const e of layout.edges) {
    const fromOff = isPointWayOffscreen(e.from, viewport);
    const toOff = isPointWayOffscreen(e.to, viewport);

    const anchor = fromOff && toOff ? null : fromOff ? e.to : toOff ? e.from : null;
    const anchorId = anchor === e.to ? e.toId : e.fromId;
    const other = anchor === e.to ? e.from : e.to;
    const otherId = anchor === e.to ? e.fromId : e.toId;

    if (!anchor) {
      continue;
    }
    const angle = Math.atan2(other.y - anchor.y, other.x - anchor.x);
    const increment = offsetIncrements[anchorId] || 0;
    offsetIncrements[anchorId] = increment + 40;

    const size = getForeignNodeDimensions(otherId);
    const ray = {
      x: anchor.x + Math.cos(angle) * (30 + size.width),
      y: anchor.y + (anchor === e.from ? 50 : -50) + (anchor === e.from ? increment : -increment),
    };

    if (!placedLabels[otherId]) {
      placedLabels[otherId] = ray;

      nodes.push(
        <foreignObject
          key={`${e.fromId}->${e.toId}`}
          x={ray.x - size.width / 2}
          y={ray.y}
          onMouseEnter={() => setHighlighted(otherId)}
          onMouseLeave={() => setHighlighted(null)}
          onClick={() => onGoToPoint(other)}
          {...size}
        >
          <ForeignNode assetKey={{path: JSON.parse(otherId)}} backgroundColor="white" />
        </foreignObject>,
      );
    }

    edges.push(
      <DashedStyledPath
        key={`${e.fromId}->${e.toId}`}
        d={buildSVGPath({source: anchor, target: placedLabels[otherId]})}
        stroke={
          e.fromId === highlighted || e.toId === highlighted ? Colors.Blue500 : 'rgba(0,0,0,0.2)'
        }
      />,
    );
  }

  return (
    <>
      {edges}
      {nodes}
    </>
  );
};

export const AssetEdges: React.FC<{edges: AssetLayoutEdge[]; color: string}> = React.memo(
  ({edges, color}) => (
    <>
      <defs>
        <marker
          id={`arrow${btoa(color)}`}
          viewBox="0 0 8 10"
          refX="1"
          refY="5"
          markerUnits="strokeWidth"
          markerWidth="4"
          orient="auto"
        >
          <path d="M 0 0 L 8 5 L 0 10 z" fill={color} />
        </marker>
      </defs>
      {edges.map((edge, idx) => (
        <StyledPath
          key={idx}
          d={buildSVGPath({source: edge.from, target: edge.to})}
          stroke={color}
          markerEnd={`url(#arrow${btoa(color)})`}
        />
      ))}
    </>
  ),
);

const StyledPath = styled('path')`
  stroke-width: 4;
  fill: none;
`;

const DashedStyledPath = styled('path')`
  stroke-width: 4;
  stroke-dasharray: 2 4;
  fill: none;
`;
