import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui';
import React from 'react';

import {createAppCache} from '../../app/AppCache';
import {RunStatus} from '../../graphql/types';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext';
import {
  AssetPartitionDetail,
  AssetPartitionDetailEmpty,
  AssetPartitionDetailLoader,
} from '../AssetPartitionDetail';
import {
  buildAssetPartitionDetailMock,
  MaterializationUpstreamDataFullMock,
} from '../__fixtures__/AssetEventDetail.fixtures';

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

export const MaterializationFollowedByObservations = () => {
  return (
    <MockedProvider
      mocks={[buildAssetPartitionDetailMock(), MaterializationUpstreamDataFullMock]}
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

export const MaterializationWithRecentFailure = () => {
  return (
    <MockedProvider
      mocks={[
        buildAssetPartitionDetailMock(RunStatus.FAILURE),
        MaterializationUpstreamDataFullMock,
      ]}
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

export const MaterializationWithInProgressRun = () => {
  return (
    <MockedProvider
      mocks={[
        buildAssetPartitionDetailMock(RunStatus.STARTING),
        MaterializationUpstreamDataFullMock,
      ]}
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
