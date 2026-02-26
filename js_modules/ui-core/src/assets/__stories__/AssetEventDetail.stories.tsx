import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';

import {createAppCache} from '../../app/AppCache';
import {StorybookProvider} from '../../testing/StorybookProvider';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {AssetEventDetail, AssetEventDetailEmpty} from '../AssetEventDetail';
import {
  BasicObservationEvent,
  MaterializationEventFull,
  MaterializationEventMinimal,
  MaterializationUpstreamDataEmptyMock,
  MaterializationUpstreamDataFullMock,
} from '../__fixtures__/AssetEventDetail.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Details/Event Detail',
  component: AssetEventDetail,
};

export const EmptyState = () => {
  return (
    <Box style={{width: '950px'}}>
      <AssetEventDetailEmpty />
    </Box>
  );
};

export const MaterializationMinimal = () => {
  return (
    <MockedProvider mocks={[MaterializationUpstreamDataEmptyMock]} cache={createAppCache()}>
      <WorkspaceProvider>
        <Box style={{width: '950px'}}>
          <AssetEventDetail assetKey={{path: ['asset_1']}} event={MaterializationEventMinimal} />
        </Box>
      </WorkspaceProvider>
    </MockedProvider>
  );
};

export const MaterializationFull = () => {
  return (
    <MockedProvider mocks={[MaterializationUpstreamDataFullMock]} cache={createAppCache()}>
      <WorkspaceProvider>
        <Box style={{width: '950px', display: 'flex', flexDirection: 'column'}}>
          <AssetEventDetail assetKey={{path: ['asset_1']}} event={MaterializationEventFull} />
        </Box>
      </WorkspaceProvider>
    </MockedProvider>
  );
};

export const Observation = () => {
  return (
    <StorybookProvider>
      <Box style={{width: '800px', display: 'flex', flexDirection: 'column'}}>
        <AssetEventDetail assetKey={{path: ['asset_1']}} event={BasicObservationEvent} />
      </Box>
    </StorybookProvider>
  );
};
