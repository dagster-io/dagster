import {Box, MetadataTable} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {StorybookProvider} from '../testing/StorybookProvider';
import {RunStatus} from '../types/globalTypes';

import {RunStatusPez, RunStatusPezList} from './RunStatusPez';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunStatusPez',
  component: RunStatusPez,
} as Meta;

const mocks = {
  RunStatsSnapshot: () => ({
    stepsSucceeded: () => 10,
    stepsFailed: () => 10,
    expectations: () => 10,
    materializations: () => 10,
  }),
};

export const Colors = () => {
  return (
    <StorybookProvider apolloProps={{mocks}}>
      <MetadataTable
        rows={Object.values(RunStatus).map((value: RunStatus) => ({
          key: value,
          value: (
            <Box padding={{top: 2}}>
              <RunStatusPez runId={faker.datatype.uuid()} status={value} />
            </Box>
          ),
        }))}
      />
    </StorybookProvider>
  );
};

export const List = () => {
  const fakeId = React.useCallback(() => faker.datatype.uuid(), []);
  const randomList = React.useCallback(
    (count) =>
      [...new Array(count)].map(() => {
        const rand = Math.random();
        const runId = fakeId();
        if (rand < 0.7) {
          return {runId, status: RunStatus.SUCCESS};
        }
        return {runId, status: RunStatus.FAILURE};
      }),
    [fakeId],
  );

  return (
    <StorybookProvider apolloProps={{mocks}}>
      <Box flex={{direction: 'column', gap: 8}}>
        <RunStatusPezList fade runs={randomList(10)} />
        <RunStatusPezList
          fade
          runs={[...randomList(9), {runId: fakeId(), status: RunStatus.STARTING}]}
        />
        <RunStatusPezList
          fade
          runs={[
            ...randomList(7),
            {runId: fakeId(), status: RunStatus.STARTING},
            {runId: fakeId(), status: RunStatus.STARTING},
            {runId: fakeId(), status: RunStatus.STARTING},
          ]}
        />
      </Box>
    </StorybookProvider>
  );
};
