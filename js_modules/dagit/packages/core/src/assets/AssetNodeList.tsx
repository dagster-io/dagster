import {Box} from '@dagster-io/ui';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AssetNode} from '../asset-graph/AssetNode';
import {LiveData, toGraphId} from '../asset-graph/Utils';

import {AssetNodeDefinitionFragment_dependencies} from './types/AssetNodeDefinitionFragment';

export const AssetNodeList: React.FC<{
  items: AssetNodeDefinitionFragment_dependencies[];
  liveDataByNode: LiveData;
}> = ({items, liveDataByNode}) => {
  const history = useHistory();

  return (
    <Container flex={{gap: 4}} padding={{horizontal: 12}}>
      {items.map(({asset}) => (
        <AssetNodeWrapper
          key={asset.id}
          onClick={(e) => {
            e.stopPropagation();
            history.push(`/instance/assets/${asset.assetKey.path.join('/')}?view=definition`);
          }}
        >
          <AssetNode
            definition={asset}
            inAssetCatalog
            selected={false}
            liveData={liveDataByNode[toGraphId(asset.assetKey)]}
          />
        </AssetNodeWrapper>
      ))}
    </Container>
  );
};

const Container = styled(Box)`
  height: 144px;
  overflow-x: auto;
  width: 100%;
  white-space: nowrap;
`;

const AssetNodeWrapper = styled.div`
  cursor: pointer;
  width: 240px;
`;
