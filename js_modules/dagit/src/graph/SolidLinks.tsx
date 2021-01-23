import {Colors} from '@blueprintjs/core';
import {pathVerticalDiagonal} from '@vx/shape';
import * as React from 'react';
import styled from 'styled-components/macro';

import {weakmapMemoize} from 'src/app/Util';
import {
  IFullPipelineLayout,
  IFullSolidLayout,
  ILayoutConnection,
} from 'src/graph/getFullSolidLayout';
import {PipelineGraphSolidFragment} from 'src/graph/types/PipelineGraphSolidFragment';

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

const edgeIsDynamic = (
  solids: PipelineGraphSolidFragment[],
  from: {solidName: string; edgeName: string},
) => {
  const solid = solids.find((s) => s.name === from.solidName);
  const outDef = solid?.definition.outputDefinitions.find((o) => o.name === from.edgeName);
  return outDef?.isDynamic || false;
};

export const SolidLinks = React.memo(
  (props: {
    opacity: number;
    solids: PipelineGraphSolidFragment[];
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
          {edgeIsDynamic(props.solids, from) && (
            <text x={to.point.x - 20} y={to.point.y + 10} width="40" style={{fontSize: 70}}>
              *
            </text>
          )}
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
