import {MockedProvider} from '@apollo/client/testing';

import {InMemoryCache} from '../../apollo-client';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import RunsFeedRoot from '../RunsFeedRoot';
import {
  RunsFeedRootMockBackfill,
  RunsFeedRootMockRuns,
} from '../__fixtures__/RunsFeedRoot.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsFeedRoot',
  component: RunsFeedRoot,
};

// This cache prevents Apollo Client from stripping fields in mock data.
const createFixingRunsCache = () => {
  return new InMemoryCache({
    possibleTypes: {
      RunsFeedEntry: ['Run', 'PartitionBackfill'],
    },
    typePolicies: {
      Run: {
        keyFields: false,
      },
      PartitionBackfill: {
        keyFields: false,
      },
    },
  });
};

export const Runs = () => {
  return (
    <MockedProvider mocks={[RunsFeedRootMockRuns]} cache={createFixingRunsCache()}>
      <WorkspaceProvider>
        <RunsFeedRoot />
      </WorkspaceProvider>
    </MockedProvider>
  );
};

export const Backfill = () => {
  return (
    <MockedProvider mocks={[RunsFeedRootMockBackfill]} cache={createFixingRunsCache()}>
      <WorkspaceProvider>
        <RunsFeedRoot />
      </WorkspaceProvider>
    </MockedProvider>
  );
};
