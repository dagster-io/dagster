import {Box, Spinner} from '@dagster-io/ui-components';
import React from 'react';
import {useHistory} from 'react-router-dom';
import styled from 'styled-components';

import {AssetNode} from '../asset-graph/AssetNode';
import {AssetNodeForGraphQueryFragment} from '../asset-graph/types/useAssetGraphData.types';

import {assetDetailsPathForKey} from './assetDetailsPathForKey';

export const AssetNodeList = ({items}: {items: AssetNodeForGraphQueryFragment[] | null}) => {
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
            history.push(assetDetailsPathForKey(asset.assetKey, {view: 'definition'}));
          }}
        >
          <AssetNode definition={asset} selected={false} />
        </AssetNodeWrapper>
      ))}
    </Container>
  );
};

const Container = styled(Box)`
  height: 195px;
  overflow-x: auto;
  width: 100%;
  white-space: nowrap;
`;

const AssetNodeWrapper = styled.div`
  cursor: pointer;
  width: 260px;
  flex-shrink: 0;
`;
