import {Meta} from '@storybook/react';

import {StorybookProvider} from '../../testing/StorybookProvider';
import {RunsFeedTableWithFilters} from '../RunsFeedTable';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunsFeedTable',
  component: RunsFeedTableWithFilters,
} as Meta;

export const Example = () => {
  const customMocks = {
    RunsFeedConnection: () => ({
      results: () => [...new Array(3)], // Generate 3 mock runs
    }),
    Run: () => ({
      jobName: () => 'example-job',
    }),
  };

  return (
    <StorybookProvider apolloProps={{mocks: customMocks}}>
      <RunsFeedTableWithFilters filter={{}} includeRunsFromBackfills={false} />
    </StorybookProvider>
  );
};
