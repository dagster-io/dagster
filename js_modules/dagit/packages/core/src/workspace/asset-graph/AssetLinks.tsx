import React from 'react';
import styled from 'styled-components/macro';

import {ColorsWIP} from '../../ui/Colors';

import {buildSVGPath, IEdge} from './Utils';

export const AssetLinks: React.FC<{edges: IEdge[]}> = React.memo(({edges}) => (
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
        <path d="M 0 0 L 8 5 L 0 10 z" fill={ColorsWIP.KeylineGray} />
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
  stroke: ${ColorsWIP.KeylineGray};
  ${({dashed}) => (dashed ? `stroke-dasharray: 8 2;` : '')}
  fill: none;
`;
