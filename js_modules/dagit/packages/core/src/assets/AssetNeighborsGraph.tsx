import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SVGViewport} from '../graph/SVGViewport';
import {AssetLinks} from '../workspace/asset-graph/AssetLinks';
import {AssetNode, getNodeDimensions} from '../workspace/asset-graph/AssetNode';
import {getForeignNodeDimensions, ForeignNode} from '../workspace/asset-graph/ForeignNode';
import {
  layoutGraph,
  buildGraphComputeStatuses,
  GraphData,
  assetKeyToString,
} from '../workspace/asset-graph/Utils';

import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

const buildGraphFromSingleNode = (assetNode: AssetNodeDefinitionFragment) => {
  const graphData: GraphData = {
    downstream: {
      [assetNode.id]: {},
    },
    nodes: {
      [assetNode.id]: {
        id: assetNode.id,
        assetKey: assetNode.assetKey,
        definition: {...assetNode, dependencies: []},
        hidden: false,
      },
    },
    upstream: {
      [assetNode.id]: {},
    },
  };

  for (const {asset} of assetNode.dependencies) {
    graphData.upstream[assetNode.id][asset.id] = true;
    graphData.downstream[asset.id] = {...graphData.downstream[asset.id], [assetNode.id]: 'a'};
    graphData.nodes[asset.id] = {
      id: asset.id,
      assetKey: asset.assetKey,
      definition: {...asset, dependencies: []},
      hidden: false,
    };
  }
  for (const {asset} of assetNode.dependedBy) {
    graphData.upstream[asset.id] = {...graphData.upstream[asset.id], [assetNode.id]: true};
    graphData.downstream[assetNode.id][asset.id] = 'a';
    graphData.nodes[asset.id] = {
      id: asset.id,
      assetKey: asset.assetKey,
      definition: {...asset, dependencies: []},
      hidden: false,
    };
  }
  return graphData;
};

export const AssetNeighborsGraph: React.FC<{assetNode: AssetNodeDefinitionFragment}> = ({
  assetNode,
}) => {
  const history = useHistory();
  const graphData = buildGraphFromSingleNode(assetNode);
  const layout = layoutGraph(graphData, 0);
  const computeStatuses = buildGraphComputeStatuses(graphData);

  return (
    <SVGViewport
      key={assetNode.id}
      interactor={SVGViewport.Interactors.None}
      graphWidth={layout.width}
      graphHeight={layout.height}
      onKeyDown={() => {}}
      onClick={() => {}}
      maxZoom={1.1}
      maxAutocenterZoom={1.0}
    >
      {({scale: _scale}: any) => (
        <SVGContainer width={layout.width} height={layout.height}>
          <AssetLinks edges={layout.edges} />
          {layout.nodes.map((layoutNode) => {
            const graphNode = graphData.nodes[layoutNode.id];
            const {width, height} = graphNode.hidden
              ? getForeignNodeDimensions(layoutNode.id)
              : getNodeDimensions(graphNode.definition);
            return (
              <foreignObject
                key={layoutNode.id}
                x={layoutNode.x}
                y={layoutNode.y}
                width={width}
                height={height}
                onClick={(e) => {
                  e.stopPropagation();
                  history.push(`/instance/assets/${assetKeyToString(graphNode.assetKey)}`);
                }}
                style={{overflow: 'visible'}}
              >
                {graphNode.hidden ? (
                  <ForeignNode assetKey={graphNode.assetKey} />
                ) : (
                  <AssetNode
                    definition={graphNode.definition}
                    metadata={[]}
                    selected={graphNode.assetKey === assetNode.assetKey}
                    computeStatus={computeStatuses[graphNode.id]}
                    secondaryHighlight={false}
                    repoAddress={{
                      name: 'a',
                      location: 'a',
                    }}
                  />
                )}
              </foreignObject>
            );
          })}
        </SVGContainer>
      )}
    </SVGViewport>
  );
};

const SVGContainer = styled.svg`
  overflow: visible;
  border-radius: 0;
`;
