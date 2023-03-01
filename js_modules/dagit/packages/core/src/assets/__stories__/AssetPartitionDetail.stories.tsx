import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui';
import React from 'react';

import {createAppCache} from '../app/AppCache';
import {WorkspaceProvider} from '../workspace/WorkspaceContext';

import {
  AssetPartitionDetailMock,
  MaterializationUpstreamDataFullMock,
} from './AssetEventDetail.mocks';
import {
  AssetPartitionDetail,
  AssetPartitionDetailEmpty,
  AssetPartitionDetailLoader,
} from './AssetPartitionDetail';

// eslint-disable-next-line import/no-default-export
export default {component: AssetPartitionDetail};

export const EmptyState = () => {
  return (
    <MockedProvider cache={createAppCache()}>
      <Box style={{width: '950px'}}>
        <AssetPartitionDetailEmpty />
      </Box>
    </MockedProvider>
  );
};

export const MaterializationFollowedByObservation = () => {
  return (
    <MockedProvider
      mocks={[AssetPartitionDetailMock, MaterializationUpstreamDataFullMock]}
      cache={createAppCache()}
    >
      <WorkspaceProvider>
        <Box style={{width: '950px'}}>
          <AssetPartitionDetailLoader assetKey={{path: ['asset_1']}} partitionKey="2022-02-02" />
        </Box>
      </WorkspaceProvider>
    </MockedProvider>
  );
};
