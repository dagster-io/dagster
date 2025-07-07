import {MockedProvider} from '@apollo/client/testing';
import {Meta} from '@storybook/react';

import {InMemoryCache} from '../../apollo-client';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import RunsFeedRoot from '../RunsFeedRoot';
import {RunsFeedRootMock} from '../__fixtures__/RunsFeedRoot.fixtures';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsFeedRoot',
  component: RunsFeedRoot,
} as Meta;

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

export const Example = () => {
  return (
    <MockedProvider mocks={[RunsFeedRootMock]} cache={createFixingRunsCache()}>
      <WorkspaceProvider>
        <RunsFeedRoot />
      </WorkspaceProvider>
    </MockedProvider>
  );
};
