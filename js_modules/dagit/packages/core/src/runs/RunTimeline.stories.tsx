import {Meta} from '@storybook/react/types-6-0';
import faker from 'faker';
import * as React from 'react';

import {RunTimeline} from '../runs/RunTimeline';
import {RunStatus} from '../types/globalTypes';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunTimeline',
  component: RunTimeline,
} as Meta;

const generateRuns = (runCount: number, range: [number, number]) => {
  const [start, end] = range;
  const now = Date.now();
  return [...new Array(6)]
    .map(() => faker.date.between(new Date(start), new Date(end)))
    .map((startDate) => {
      const endTime = Math.min(startDate.getTime() + faker.datatype.number() * 10, now);
      const status =
        endTime === now
          ? RunStatus.STARTED
          : faker.random.arrayElement([RunStatus.SUCCESS, RunStatus.FAILURE]);

      return {
        id: faker.datatype.uuid(),
        status,
        startTime: startDate.getTime(),
        endTime,
      };
    });
};

export const OneRow = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    return {
      [jobKey]: {label: jobKey, path: `/${jobKey}`, runs: generateRuns(6, [twoHoursAgo, now])},
    };
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const RowWithOverlappingRuns = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const [first, second, third] = generateRuns(3, [twoHoursAgo, now]);
    return {
      [jobKey]: {
        label: jobKey,
        path: `/${jobKey}`,
        runs: [{...first}, {...first}, {...second}, {...second}, {...second}, third],
      },
    };
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const ManyRows = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    return [...new Array(12)].reduce((accum) => {
      const jobKey = faker.random.words(3).split(' ').join('-').toLowerCase();
      return {...accum, [jobKey]: {path: `/${jobKey}`, runs: generateRuns(6, [twoHoursAgo, now])}};
    }, {});
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
    return {
      [jobKeyA]: {
        label: jobKeyA,
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
      [jobKeyB]: {
        label: jobKeyB,
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
    };
  }, [twoDaysAgo, twoHoursAgo]);

  return <RunTimeline jobs={jobs} range={[fourHoursAgo, future]} />;
};
