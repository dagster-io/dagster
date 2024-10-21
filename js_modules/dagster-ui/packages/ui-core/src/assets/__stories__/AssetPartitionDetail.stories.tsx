import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';

import {createAppCache} from '../../app/AppCache';
import {RunStatus, buildStaleCause} from '../../graphql/types';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {
  AssetPartitionDetail,
  AssetPartitionDetailEmpty,
  AssetPartitionDetailLoader,
} from '../AssetPartitionDetail';
import {
  MaterializationUpstreamDataFullMock,
  buildAssetPartitionDetailMock,
  buildAssetPartitionStaleMock,
} from '../__fixtures__/AssetEventDetail.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Partition Detail',
  component: AssetPartitionDetail,
};

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
      mocks={[
        buildAssetPartitionDetailMock(),
        buildAssetPartitionStaleMock(),
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

export const MaterializationWithRecentFailure = () => {
  return (
    <MockedProvider
      mocks={[
        buildAssetPartitionDetailMock(RunStatus.FAILURE),
        buildAssetPartitionStaleMock([buildStaleCause()]),
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
        buildAssetPartitionStaleMock(),
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
