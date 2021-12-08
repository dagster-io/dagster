import * as React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {SVGViewport} from '../graph/SVGViewport';
import {AssetLinks} from '../workspace/asset-graph/AssetLinks';
import {AssetNode} from '../workspace/asset-graph/AssetNode';
import {ForeignNode} from '../workspace/asset-graph/ForeignNode';
import {
  layoutGraph,
  GraphData,
  displayNameForAssetKey,
  LiveData,
} from '../workspace/asset-graph/Utils';
import {RepoAddress} from '../workspace/types';

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
        definition: {...assetNode, dependencies: [], dependedBy: []},
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
      definition: {...asset, dependencies: [], dependedBy: []},
      hidden: false,
    };
  }
  for (const {asset} of assetNode.dependedBy) {
    graphData.upstream[asset.id] = {...graphData.upstream[asset.id], [assetNode.id]: true};
    graphData.downstream[assetNode.id][asset.id] = 'a';
    graphData.nodes[asset.id] = {
      id: asset.id,
      assetKey: asset.assetKey,
      definition: {...asset, dependencies: [], dependedBy: []},
      hidden: false,
    };
  }
  return graphData;
};

export const AssetNeighborsGraph: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  repoAddress: RepoAddress;
  liveDataByNode: LiveData;
}> = ({assetNode, liveDataByNode, repoAddress}) => {
  const history = useHistory();
  const graphData = buildGraphFromSingleNode(assetNode);
  const layout = layoutGraph(graphData, {margin: 0, mini: true});

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
            return (
              <foreignObject
                {...layoutNode}
                key={layoutNode.id}
                style={{overflow: 'visible'}}
                onClick={(e) => {
                  e.stopPropagation();
                  if (graphNode.definition.opName) {
                    history.push(`/instance/assets/${graphNode.assetKey.path.join('/')}`);
                  }
                }}
              >
                {graphNode.hidden || !graphNode.definition.opName ? (
                  <ForeignNode assetKey={graphNode.assetKey} />
                ) : (
                  <AssetNode
                    definition={graphNode.definition}
                    metadata={[]}
                    selected={graphNode.assetKey === assetNode.assetKey}
                    liveData={liveDataByNode[graphNode.id]}
                    secondaryHighlight={false}
                    repoAddress={repoAddress}
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
