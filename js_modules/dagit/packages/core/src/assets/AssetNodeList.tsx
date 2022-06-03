import {Box, Spinner} from '@dagster-io/ui';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AssetNode} from '../asset-graph/AssetNode';
import {LiveData, toGraphId} from '../asset-graph/Utils';
import {AssetGraphQuery_assetNodes} from '../asset-graph/types/AssetGraphQuery';

export const AssetNodeList: React.FC<{
  items: AssetGraphQuery_assetNodes[] | null;
  liveDataByNode: LiveData;
}> = ({items, liveDataByNode}) => {
  const history = useHistory();

  if (items === null) {
    return (
      <Container flex={{alignItems: 'center', justifyContent: 'center'}}>
        <Spinner purpose="section" />
      </Container>
    );
  }

  return (
    <Container flex={{gap: 4}} padding={{horizontal: 12}}>
      {items.map((asset) => (
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
  flex-shrink: 0;
`;
