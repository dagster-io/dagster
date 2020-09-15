import * as React from 'react';
import {Colors} from '@blueprintjs/core';
import {pathVerticalDiagonal} from '@vx/shape';
import {ILayoutConnection, IFullPipelineLayout, IFullSolidLayout} from './getFullSolidLayout';
import styled from 'styled-components/macro';
import {weakmapMemoize} from '../Util';

export type Edge = {a: string; b: string};

const buildSVGPath = pathVerticalDiagonal({
  source: (s: any) => s.source,
  target: (s: any) => s.target,
  x: (s: any) => s.x,
  y: (s: any) => s.y,
});

const buildSVGPaths = weakmapMemoize(
  (connections: ILayoutConnection[], solids: {[name: string]: IFullSolidLayout}) =>
    connections.map(({from, to}) => ({
      path: buildSVGPath({
        // can also use from.point for the "Dagre" closest point on node
        source: solids[from.solidName].outputs[from.edgeName].port,
        target: solids[to.solidName].inputs[to.edgeName].port,
      }),
      from,
      to,
    })),
);

export const SolidLinks = React.memo(
  (props: {
    opacity: number;
    layout: IFullPipelineLayout;
    connections: ILayoutConnection[];
    onHighlight: (arr: Edge[]) => void;
  }) => (
    <g opacity={props.opacity}>
      {buildSVGPaths(props.connections, props.layout.solids).map(({path, from, to}, idx) => (
        <g
          key={idx}
          onMouseLeave={() => props.onHighlight([])}
          onMouseEnter={() => props.onHighlight([{a: from.solidName, b: to.solidName}])}
        >
          <StyledPath d={path} />
        </g>
      ))}
    </g>
  ),
);

SolidLinks.displayName = 'SolidLinks';

const StyledPath = styled('path')`
  stroke-width: 6;
  stroke: ${Colors.BLACK};
  fill: none;
`;
