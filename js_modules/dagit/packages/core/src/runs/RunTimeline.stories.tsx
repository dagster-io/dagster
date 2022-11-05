import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {RunTimeline, TimelineJob} from '../runs/RunTimeline';
import {generateRunMocks} from '../testing/generateRunMocks';
import {RunStatus} from '../types/globalTypes';
import {buildRepoAddress} from '../workspace/buildRepoAddress';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunTimeline',
  component: RunTimeline,
} as Meta;

const makeRepoAddress = () =>
  buildRepoAddress(faker.random.words(1).toLowerCase(), faker.random.words(1).toLowerCase());

export const OneRow = () => {
  const sixHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs: TimelineJob[] = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: jobKey,
        jobName: jobKey,
        jobType: 'job',
        path: `/${jobKey}`,
        repoAddress,
        runs: generateRunMocks(6, [sixHoursAgo, now]),
      },
    ];
  }, [sixHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[sixHoursAgo, now]} />;
};

export const RowWithOverlappingRuns = () => {
  const sixHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs: TimelineJob[] = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    const [first, second, third] = generateRunMocks(3, [sixHoursAgo, now]);
    return [
      {
        key: jobKey,
        jobName: jobKey,
        jobType: 'job',
        path: `/${jobKey}`,
        repoAddress,
        runs: [{...first}, {...first}, {...second}, {...second}, {...second}, third],
      },
    ];
  }, [sixHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[sixHoursAgo, now]} />;
};

export const OverlapWithRunning = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs: TimelineJob[] = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: jobKey,
        jobName: jobKey,
        jobType: 'job',
        path: `/${jobKey}`,
        repoAddress,
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

  const jobs: TimelineJob[] = React.useMemo(() => {
    const repoAddress = makeRepoAddress();
    return [...new Array(12)].reduce((accum) => {
      const jobKey = faker.random.words(3).split(' ').join('-').toLowerCase();
      return [
        ...accum,
        {
          key: jobKey,
          jobName: jobKey,
          path: `/${jobKey}`,
          repoAddress,
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

  const jobs: TimelineJob[] = React.useMemo(() => {
    const repoAddress = makeRepoAddress();
    const jobKeyA = faker.random.words(2).split(' ').join('-').toLowerCase();
    const jobKeyB = faker.random.words(2).split(' ').join('-').toLowerCase();
    return [
      {
        key: jobKeyA,
        jobName: jobKeyA,
        jobType: 'job',
        path: `/${jobKeyA}`,
        repoAddress,
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
        jobType: 'job',
        path: `/${jobKeyB}`,
        repoAddress,
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

export const MultipleStatusesBatched = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs: TimelineJob[] = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: jobKey,
        jobName: jobKey,
        jobType: 'job',
        path: `/${jobKey}`,
        repoAddress,
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
            status: RunStatus.FAILURE,
            startTime: twoHoursAgo + 60 * 60 * 1000,
            endTime: now,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 60 * 60 * 1000,
            endTime: now,
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

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const BatchThresholdTesting = () => {
  const threeHoursAgo = React.useMemo(() => Date.now() - 3 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs: TimelineJob[] = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: jobKey,
        jobName: jobKey,
        jobType: 'job',
        path: `/${jobKey}`,
        repoAddress,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now,
            endTime: now + 5 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 2 * 1000,
            endTime: now + 60 * 2 * 1000 + 5 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 4 * 1000,
            endTime: now + 60 * 4 * 1000 + 5 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 6 * 1000,
            endTime: now + 60 * 6 * 1000 + 5 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 8 * 1000,
            endTime: now + 60 * 8 * 1000 + 5 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: threeHoursAgo + 24 * 60 * 1000,
            endTime: threeHoursAgo + 26 * 60 * 1000,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.FAILURE,
            startTime: threeHoursAgo + 28 * 60 * 1000,
            endTime: threeHoursAgo + 30 * 60 * 1000,
          },
        ],
      },
    ];
  }, [threeHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[threeHoursAgo, now + 60 * 60 * 1000]} />;
};
