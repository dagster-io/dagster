import {Colors} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {buildSVGPath} from './Utils';
import {AssetLayoutEdge} from './layout';

export const AssetConnectedEdges: React.FC<{
  edges: AssetLayoutEdge[];
  highlighted: string | null;
}> = ({edges, highlighted}) => {
  // Note: we render the highlighted edges twice, but it's so that the first item with
  // all the edges in it can remain memoized.
  return (
    <React.Fragment>
      <AssetEdges color={Colors.KeylineGray} edges={edges} />
      <AssetEdges
        color={Colors.Blue500}
        edges={edges.filter(({fromId, toId}) => highlighted === fromId || highlighted === toId)}
      />
    </React.Fragment>
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
