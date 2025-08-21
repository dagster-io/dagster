import {Box} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {RunsFeedRootNew} from '../RunsFeedRootNew';
import {StorybookProvider} from '../../testing/StorybookProvider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsFeedRootNew',
  component: RunsFeedRootNew,
  parameters: {
    chromatic: {disableSnapshot: false},
  },
} as Meta;

export const Default = () => {
  const customMocks = {
    RunsFeedConnection: () => ({
      results: () => [...new Array(100)], // Generate 100 mock runs
      cursor: () => 'cursor-123',
      hasMore: () => true,
    }),
    RunsFeedCount: () => ({
      count: () => 150,
    }),
    // Don't override Run - let it use the rich defaultMocks
  };

  return (
    <StorybookProvider apolloProps={{mocks: customMocks}}>
      <Box style={{height: '800px', width: '100%'}}>
        <RunsFeedRootNew />
      </Box>
    </StorybookProvider>
  );
};

export const Loading = () => {
  // Empty mocks to trigger loading state
  return (
    <StorybookProvider>
      <Box style={{height: '800px', width: '100%'}}>
        <RunsFeedRootNew />
      </Box>
    </StorybookProvider>
  );
};