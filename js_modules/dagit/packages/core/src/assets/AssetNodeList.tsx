import {Box} from '@dagster-io/ui';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {AssetNode} from '../workspace/asset-graph/AssetNode';
import {ForeignNode} from '../workspace/asset-graph/ForeignNode';
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
              history.push(`/instance/assets/${asset.assetKey.path.join('/')}`);
            }}
          >
            {asset.jobs.length ? (
              <AssetNode
                definition={asset}
                metadata={[]}
                inAssetCatalog
                jobName={asset.jobs[0].name}
                selected={false}
                liveData={liveDataByNode[asset.id]}
              />
            ) : (
              <ForeignNode assetKey={asset.assetKey} />
            )}
          </div>
        );
      })}
    </Box>
  );
};
