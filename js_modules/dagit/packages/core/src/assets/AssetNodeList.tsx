import {Box} from '@dagster-io/ui';
import React from 'react';
import {useHistory} from 'react-router-dom';

import {AssetNode} from '../workspace/asset-graph/AssetNode';
import {ForeignNode} from '../workspace/asset-graph/ForeignNode';
import {LiveData, toGraphId} from '../workspace/asset-graph/Utils';

import {AssetNodeDefinitionFragment_dependencies} from './types/AssetNodeDefinitionFragment';

export const AssetNodeList: React.FC<{
  items: AssetNodeDefinitionFragment_dependencies[];
  liveDataByNode: LiveData;
}> = ({items, liveDataByNode}) => {
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
              history.push(`/instance/assets/${asset.assetKey.path.join('/')}?view=definition`);
            }}
          >
            {asset.jobNames.length ? (
              <AssetNode
                definition={asset}
                metadata={[]}
                inAssetCatalog
                jobName={asset.jobNames[0]}
                selected={false}
                liveData={liveDataByNode[toGraphId(asset.assetKey)]}
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
