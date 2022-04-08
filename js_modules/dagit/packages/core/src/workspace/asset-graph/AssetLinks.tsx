import {Colors} from '@dagster-io/ui';
import React from 'react';
import styled from 'styled-components/macro';

import {buildSVGPath} from './Utils';
import {AssetLayoutEdge} from './layout';

export const AssetLinks: React.FC<{edges: AssetLayoutEdge[]}> = React.memo(({edges}) => (
  <>
    <defs>
      <marker
        id="arrow"
        viewBox="0 0 8 10"
        refX="1"
        refY="5"
        markerUnits="strokeWidth"
        markerWidth="4"
        orient="auto"
      >
        <path d="M 0 0 L 8 5 L 0 10 z" fill={Colors.KeylineGray} />
      </marker>
    </defs>
    {edges.map((edge, idx) => (
      <StyledPath
        key={idx}
        d={buildSVGPath({source: edge.from, target: edge.to})}
        dashed={edge.dashed}
        markerEnd="url(#arrow)"
      />
    ))}
  </>
));

const StyledPath = styled('path')<{dashed: boolean}>`
  stroke-width: 4;
  stroke: ${Colors.KeylineGray};
  ${({dashed}) => (dashed ? `stroke-dasharray: 8 2;` : '')}
  fill: none;
`;
