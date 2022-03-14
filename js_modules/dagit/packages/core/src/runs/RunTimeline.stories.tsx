import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {RunTimeline} from '../runs/RunTimeline';
import {generateRunMocks} from '../testing/generateRunMocks';
import {RunStatus} from '../types/globalTypes';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunTimeline',
  component: RunTimeline,
} as Meta;

export const OneRow = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    return [
      {
        key: jobKey,
        jobName: jobKey,
        path: `/${jobKey}`,
        runs: generateRunMocks(6, [twoHoursAgo, now]),
      },
    ];
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const RowWithOverlappingRuns = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const [first, second, third] = generateRunMocks(3, [twoHoursAgo, now]);
    return [
      {
        key: jobKey,
        jobName: jobKey,
        path: `/${jobKey}`,
        runs: [{...first}, {...first}, {...second}, {...second}, {...second}, third],
      },
    ];
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const ManyRows = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    return [...new Array(12)].reduce((accum) => {
      const jobKey = faker.random.words(3).split(' ').join('-').toLowerCase();
      return [
        ...accum,
        {
          key: jobKey,
          jobName: jobKey,
          path: `/${jobKey}`,
          runs: generateRunMocks(6, [twoHoursAgo, now]),
        },
      ];
    }, []);
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const VeryLongRunning = () => {
  const fourHoursAgo = React.useMemo(() => Date.now() - 4 * 60 * 60 * 1000, []);
  const twoHoursAgo = React.useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
  const twoDaysAgo = React.useMemo(() => Date.now() - 48 * 60 * 60 * 1000, []);
  const future = React.useMemo(() => Date.now() + 1 * 60 * 60 * 1000, []);

  const jobs = React.useMemo(() => {
    const jobKeyA = faker.random.words(2).split(' ').join('-').toLowerCase();
    const jobKeyB = faker.random.words(2).split(' ').join('-').toLowerCase();
    return [
      {
        key: jobKeyA,
        jobName: jobKeyA,
        path: `/${jobKeyA}`,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: RunStatus.FAILURE,
            startTime: twoDaysAgo,
            endTime: twoHoursAgo,
          },
        ],
      },
      {
        key: jobKeyB,
        jobName: jobKeyB,
        path: `/${jobKeyB}`,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: RunStatus.STARTED,
            startTime: twoDaysAgo,
            endTime: Date.now(),
          },
        ],
      },
    ];
  }, [twoDaysAgo, twoHoursAgo]);

  return <RunTimeline jobs={jobs} range={[fourHoursAgo, future]} />;
};
