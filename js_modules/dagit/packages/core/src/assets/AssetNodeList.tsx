import React from 'react';
import {useHistory} from 'react-router-dom';

import {Box} from '../ui/Box';
import {AssetNode} from '../workspace/asset-graph/AssetNode';
import {LiveData} from '../workspace/asset-graph/Utils';
import {RepoAddress} from '../workspace/types';

import {AssetNodeDefinitionFragment_dependencies} from './types/AssetNodeDefinitionFragment';

export const AssetNodeList: React.FC<{
  items: AssetNodeDefinitionFragment_dependencies[];
  repoAddress: RepoAddress;
  liveDataByNode: LiveData;
}> = ({items, liveDataByNode, repoAddress}) => {
  const history = useHistory();

  return (
    <Box
      flex={{gap: 5}}
      padding={{horizontal: 12}}
      style={{
        height: 112,
        overflowX: 'auto',
        width: '100%',
        whiteSpace: 'nowrap',
      }}
    >
      {items.map(({asset}) => {
        return (
          <div
            key={asset.id}
            style={{position: 'relative', flexShrink: 0, width: 240, height: 90}}
            onClick={(e) => {
              e.stopPropagation();
              if (asset.opName) {
                history.push(`/instance/assets/${asset.assetKey.path.join('/')}`);
              }
            }}
          >
            <AssetNode
              definition={{...asset, description: null}}
              metadata={[]}
              selected={false}
              liveData={liveDataByNode[asset.id]}
              secondaryHighlight={false}
              repoAddress={repoAddress}
            />
          </div>
        );
      })}
    </Box>
  );
};
