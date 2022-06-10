import * as React from 'react';
import styled from 'styled-components/macro';

import {weakmapMemoize} from '../app/Util';
import {buildSVGPath} from '../asset-graph/Utils';

import {OpGraphLayout, OpLayout, OpLayoutEdge} from './asyncGraphLayout';
import {OpGraphOpFragment} from './types/OpGraphOpFragment';

export type Edge = {a: string; b: string};

const buildSVGPaths = weakmapMemoize((edges: OpLayoutEdge[], nodes: {[name: string]: OpLayout}) =>
  edges.map(({from, to}) => {
    const sourceOutput = nodes[from.opName].outputs[from.edgeName];
    if (!sourceOutput) {
      throw new Error(
        `Cannot find ${from.opName}:${from.edgeName} for edge to ${to.opName}:${to.edgeName}`,
      );
    }
    const targetInput = nodes[to.opName].inputs[to.edgeName];
    if (!targetInput) {
      throw new Error(
        `Cannot find ${to.opName}:${to.edgeName} for edge from ${from.opName}:${from.edgeName}`,
      );
    }
    return {
      // can also use from.point for the "Dagre" closest point on node
      path: buildSVGPath({
        source: sourceOutput.port,
        target: targetInput.port,
      }),
      sourceOutput,
      targetInput,
      from,
      to,
    };
  }),
);

const outputIsDynamic = (ops: OpGraphOpFragment[], from: {opName: string; edgeName: string}) => {
  const op = ops.find((s) => s.name === from.opName);
  const outDef = op?.definition.outputDefinitions.find((o) => o.name === from.edgeName);
  return outDef?.isDynamic || false;
};

const inputIsDynamicCollect = (
  ops: OpGraphOpFragment[],
  to: {opName: string; edgeName: string},
) => {
  const op = ops.find((s) => s.name === to.opName);
  const inputDef = op?.inputs.find((o) => o.definition.name === to.edgeName);
  return inputDef?.isDynamicCollect || false;
};

export const OpEdges = React.memo(
  (props: {
    color: string;
    ops: OpGraphOpFragment[];
    layout: OpGraphLayout;
    edges: OpLayoutEdge[];
    onHighlight: (arr: Edge[]) => void;
  }) => (
    <g>
      {buildSVGPaths(props.edges, props.layout.nodes).map(
        ({path, from, sourceOutput, targetInput, to}, idx) => (
          <g
            key={idx}
            onMouseLeave={() => props.onHighlight([])}
            onMouseEnter={() => props.onHighlight([{a: from.opName, b: to.opName}])}
          >
            <StyledPath d={path} style={{stroke: props.color}} />
            {outputIsDynamic(props.ops, from) && (
              <DynamicMarker
                color={props.color}
                x={sourceOutput.layout.x}
                y={sourceOutput.layout.y}
                direction="output"
              />
            )}
            {inputIsDynamicCollect(props.ops, to) && (
              <DynamicMarker
                color={props.color}
                x={targetInput.layout.x}
                y={targetInput.layout.y}
                direction="collect"
              />
            )}
          </g>
        ),
      )}
    </g>
  ),
);

OpEdges.displayName = 'OpEdges';

const DynamicMarker: React.FC<{
  x: number;
  y: number;
  direction: 'output' | 'collect';
  color: string;
}> = ({x, y, direction, color}) => (
  <g
    fill={color}
    transform={`translate(${x - 35}, ${y})${
      direction === 'collect' ? ',rotate(180),translate(-20, -40)' : ''
    }`}
  >
    <title>{direction === 'output' ? 'DynamicOutput' : 'DynamicCollect'}</title>
    <polygon points="14.2050781 21 14.0400391 15.2236328 18.953125 18.2705078 20.984375 14.7285156 15.8935547 11.9736328 20.984375 9.21875 18.953125 5.68945312 14.0400391 8.72363281 14.2050781 2.95996094 10.1425781 2.95996094 10.2949219 8.72363281 5.38183594 5.68945312 3.36328125 9.21875 8.45410156 11.9736328 3.36328125 14.7285156 5.38183594 18.2705078 10.2949219 15.2236328 10.1425781 21"></polygon>
    <polygon points="18.6367188 35.1669922 20.8203125 32.9707031 12.0605469 24.2109375 3.28808594 32.9707031 5.47167969 35.1669922 12.0605469 28.5908203"></polygon>
  </g>
);

const StyledPath = styled('path')`
  stroke-width: 4;
  fill: none;
`;
