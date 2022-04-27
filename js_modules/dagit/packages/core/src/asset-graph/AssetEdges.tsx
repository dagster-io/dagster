import {Colors} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {buildSVGPath} from './Utils';
import {AssetLayoutEdge} from './layout';

export const AssetEdges: React.FC<{edges: AssetLayoutEdge[]; extradark: boolean}> = React.memo(
  ({edges, extradark}) => (
    <>
      <defs>
        <marker
          id="arrow"
          viewBox="0 0 8 10"
          refX="1"
          refY="5"
          markerUnits="strokeWidth"
          markerWidth={extradark ? '6' : '4'}
          orient="auto"
        >
          <path d="M 0 0 L 8 5 L 0 10 z" fill={extradark ? Colors.Gray400 : Colors.KeylineGray} />
        </marker>
      </defs>
      {edges.map((edge, idx) =>
        extradark ? (
          <ExtraDarkStyledPath
            key={idx}
            d={buildSVGPath({source: edge.from, target: edge.to})}
            dashed={edge.dashed}
            markerEnd="url(#arrow)"
          />
        ) : (
          <StyledPath
            key={idx}
            d={buildSVGPath({source: edge.from, target: edge.to})}
            dashed={edge.dashed}
            markerEnd="url(#arrow)"
          />
        ),
      )}
    </>
  ),
);

const StyledPath = styled('path')<{dashed: boolean}>`
  stroke-width: 4;
  stroke: ${Colors.KeylineGray};
  ${({dashed}) => (dashed ? `stroke-dasharray: 8 2;` : '')}
  fill: none;
`;

const ExtraDarkStyledPath = styled('path')<{dashed: boolean}>`
  stroke-width: 8;
  stroke: ${Colors.Gray400};
  ${({dashed}) => (dashed ? `stroke-dasharray: 8 2;` : '')}
  fill: none;
`;
