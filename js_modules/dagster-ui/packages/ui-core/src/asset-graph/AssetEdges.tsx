import {Colors} from '@dagster-io/ui-components';
import React from 'react';

import {buildSVGPath} from './Utils';
import {AssetLayoutEdge} from './layout';

export const AssetEdges: React.FC<{
  edges: AssetLayoutEdge[];
  highlighted: string | null;
  strokeWidth?: number;
  baseColor?: string;
  viewportRect: {top: number; left: number; right: number; bottom: number};
}> = ({edges, highlighted, strokeWidth = 4, baseColor = Colors.KeylineGray, viewportRect}) => {
  // Note: we render the highlighted edges twice, but it's so that the first item with
  // all the edges in it can remain memoized.
  return (
    <React.Fragment>
      <AssetEdgeSet
        color={baseColor}
        edges={edges}
        strokeWidth={strokeWidth}
        viewportRect={viewportRect}
      />
      <AssetEdgeSet
        viewportRect={viewportRect}
        color={Colors.Blue500}
        edges={edges.filter(({fromId, toId}) => highlighted === fromId || highlighted === toId)}
        strokeWidth={strokeWidth}
      />
    </React.Fragment>
  );
};

const AssetEdgeSet: React.FC<{
  edges: AssetLayoutEdge[];
  color: string;
  strokeWidth: number;
  viewportRect: {top: number; left: number; right: number; bottom: number};
}> = React.memo(({edges, color, strokeWidth, viewportRect}) => (
  <>
    <defs>
      <marker
        id={`arrow${btoa(color)}`}
        viewBox="0 0 8 10"
        refX="1"
        refY="5"
        markerUnits="strokeWidth"
        markerWidth={strokeWidth}
        orient="auto"
      >
        <path d="M 0 0 L 8 5 L 0 10 z" fill={color} />
      </marker>
    </defs>
    {edges
      .filter(
        (edge) =>
          doesViewportContainPoint(edge.from, viewportRect) ||
          doesViewportContainPoint(edge.to, viewportRect),
      )
      .map((edge, idx) => (
        <path
          key={idx}
          d={buildSVGPath({source: edge.from, target: edge.to})}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          markerEnd={`url(#arrow${btoa(color)})`}
        />
      ))}
  </>
));

function doesViewportContainPoint(
  point: {x: number; y: number},
  viewportRect: {top: number; left: number; right: number; bottom: number},
) {
  return (
    point.x >= viewportRect.left &&
    point.x <= viewportRect.right &&
    point.y >= viewportRect.top &&
    point.y <= viewportRect.bottom
  );
}
