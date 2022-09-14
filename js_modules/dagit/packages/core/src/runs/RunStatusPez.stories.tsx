import {Box, MetadataTable} from '@dagster-io/ui';
import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {StorybookProvider} from '../testing/StorybookProvider';
import {generateRunMocks} from '../testing/generateRunMocks';
import {RunStatus} from '../types/globalTypes';

import {RunStatusPez, RunStatusPezList} from './RunStatusPez';
import {RunTimeFragment} from './types/RunTimeFragment';

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
  const tenDaysAgo = React.useMemo(() => Date.now() - 10 * 24 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const wrapToFragment = (
    inp: {
      id: string;
      status: RunStatus;
      startTime: number;
      endTime: number;
    }[],
  ): RunTimeFragment[] =>
    inp.map((r) => ({...r, runId: r.id, updateTime: null, __typename: 'Run'}));

  const fakeRepo = 'a_repo.py';
  const fakeId = React.useCallback(() => faker.datatype.uuid(), []);

  return (
    <StorybookProvider apolloProps={{mocks}}>
      <Box flex={{direction: 'column', gap: 8}}>
        <RunStatusPezList
          jobName={fakeRepo}
          fade
          runs={wrapToFragment(generateRunMocks(10, [tenDaysAgo, now]))}
        />
        <RunStatusPezList
          jobName={fakeRepo}
          fade
          runs={wrapToFragment(generateRunMocks(9, [tenDaysAgo, now])).map((f) => ({
            ...f,
            status: RunStatus.STARTED,
          }))}
        />
        <RunStatusPezList
          jobName={fakeRepo}
          fade
          runs={[
            ...wrapToFragment(generateRunMocks(7, [tenDaysAgo, now])),
            ...[...new Array(3)]
              .map((_, idx) => {
                const id = fakeId();
                return {
                  __typename: 'Run' as const,
                  id,
                  runId: id,
                  status: RunStatus.STARTING,
                  startTime: Date.now() - (idx + 1) * 60 * 60 * 1000,
                  endTime: Date.now() - idx * 60 * 60 * 1000,
                  updateTime: null,
                };
              })
              .reverse(), //Latest first
          ]}
        />
      </Box>
    </StorybookProvider>
  );
};
