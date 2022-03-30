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
  const sixHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    return [
      {
        key: jobKey,
        jobName: jobKey,
        path: `/${jobKey}`,
        runs: generateRunMocks(6, [sixHoursAgo, now]),
      },
    ];
  }, [sixHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[sixHoursAgo, now]} />;
};

export const RowWithOverlappingRuns = () => {
  const sixHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const [first, second, third] = generateRunMocks(3, [sixHoursAgo, now]);
    return [
      {
        key: jobKey,
        jobName: jobKey,
        path: `/${jobKey}`,
        runs: [{...first}, {...first}, {...second}, {...second}, {...second}, third],
      },
    ];
  }, [sixHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[sixHoursAgo, now]} />;
};

export const OverlapWithRunning = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    return [
      {
        key: jobKey,
        jobName: jobKey,
        path: `/${jobKey}`,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 20 * 60 * 1000,
            endTime: twoHoursAgo + 95 * 60 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 90 * 60 * 1000,
            endTime: twoHoursAgo + 110 * 60 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.STARTED,
            startTime: twoHoursAgo + 60 * 60 * 1000,
            endTime: now,
          },
        ],
      },
    ];
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now + 60 * 6000]} />;
};

export const ManyRows = () => {
  const sixHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
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
          runs: generateRunMocks(6, [sixHoursAgo, now]),
        },
      ];
    }, []);
  }, [sixHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[sixHoursAgo, now]} />;
};

export const VeryLongRunning = () => {
  const fourHoursAgo = React.useMemo(() => Date.now() - 4 * 60 * 60 * 1000, []);
  const sixHoursAgo = React.useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
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
            endTime: sixHoursAgo,
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
  }, [twoDaysAgo, sixHoursAgo]);

  return <RunTimeline jobs={jobs} range={[fourHoursAgo, future]} />;
};
