import {Box} from '@dagster-io/ui-components';
import {Meta} from '@storybook/react';

import {RunsFeedTableNewWithFilters} from '../RunsFeedTableNew';
import {StorybookProvider} from '../../testing/StorybookProvider';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsFeedTableNew',
  component: RunsFeedTableNewWithFilters,
  parameters: {
    chromatic: {disableSnapshot: false},
  },
} as Meta;

export const Default = () => {
  const customMocks = {
    RunsFeedConnection: () => ({
      results: () => [...new Array(15)], // Generate 15 mock runs
      cursor: () => 'cursor-123',
      hasMore: () => true,
    }),
    Run: () => ({
      jobName: () => 'example-data-pipeline',
    }),
  };

  return (
    <StorybookProvider apolloProps={{mocks: customMocks}}>
      <Box style={{height: '600px', width: '100%'}}>
        <RunsFeedTableNewWithFilters filter={{}} includeRunsFromBackfills={false} />
      </Box>
    </StorybookProvider>
  );
};

export const Loading = () => {
  // Empty mocks to trigger loading state
  return (
    <StorybookProvider>
      <Box style={{height: '600px', width: '100%'}}>
        <RunsFeedTableNewWithFilters filter={{}} includeRunsFromBackfills={false} />
      </Box>
    </StorybookProvider>
  );
};

export const WithManyRuns = () => {
  const customMocks = {
    RunsFeedConnection: () => ({
      results: () => [...new Array(50)], // Generate 50 mock runs
      cursor: () => 'cursor-456',
      hasMore: () => true,
    }),
    Run: () => ({
      jobName: () => 'large-dataset-processing',
    }),
  };

  return (
    <StorybookProvider apolloProps={{mocks: customMocks}}>
      <Box style={{height: '600px', width: '100%'}}>
        <RunsFeedTableNewWithFilters filter={{}} includeRunsFromBackfills={false} />
      </Box>
    </StorybookProvider>
  );
};