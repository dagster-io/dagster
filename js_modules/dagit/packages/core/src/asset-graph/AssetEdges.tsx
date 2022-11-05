import {Colors} from '@dagster-io/ui';
import React from 'react';

import {buildSVGPath} from './Utils';
import {AssetLayoutEdge} from './layout';

export const AssetEdges: React.FC<{
  edges: AssetLayoutEdge[];
  highlighted: string | null;
  strokeWidth?: number;
  baseColor?: string;
}> = ({edges, highlighted, strokeWidth = 4, baseColor = Colors.KeylineGray}) => {
  // Note: we render the highlighted edges twice, but it's so that the first item with
  // all the edges in it can remain memoized.
  return (
    <React.Fragment>
      <AssetEdgeSet color={baseColor} edges={edges} strokeWidth={strokeWidth} />
      <AssetEdgeSet
        color={Colors.Blue500}
        edges={edges.filter(({fromId, toId}) => highlighted === fromId || highlighted === toId)}
        strokeWidth={strokeWidth}
      />
    </React.Fragment>
  );
};

export const AssetEdgeSet: React.FC<{
  edges: AssetLayoutEdge[];
  color: string;
  strokeWidth: number;
}> = React.memo(({edges, color, strokeWidth}) => (
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
    {edges.map((edge, idx) => (
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
