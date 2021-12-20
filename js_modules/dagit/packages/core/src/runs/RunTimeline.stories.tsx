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
  return [...new Array(6)]
    .map(() => faker.date.between(new Date(start), new Date(end)))
    .map((startDate) => ({
      id: faker.datatype.uuid(),
      status: faker.random.arrayElement([RunStatus.SUCCESS, RunStatus.FAILURE]),
      startTime: startDate.getTime(),
      endTime: startDate.getTime() + faker.datatype.number() * 10,
    }));
};

export const OneRow = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    return {[jobKey]: generateRuns(6, [twoHoursAgo, now])};
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const RowWithOverlappingRuns = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const [first, second, third] = generateRuns(3, [twoHoursAgo, now]);
    return {[jobKey]: [{...first}, {...first}, {...second}, {...second}, {...second}, third]};
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};

export const ManyRows = () => {
  const twoHoursAgo = React.useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = React.useMemo(() => Date.now(), []);

  const jobs = React.useMemo(() => {
    return [...new Array(12)].reduce((accum) => {
      const jobKey = faker.random.words(2).split(' ').join('-').toLowerCase();
      return {...accum, [jobKey]: generateRuns(6, [twoHoursAgo, now])};
    }, {});
  }, [twoHoursAgo, now]);

  return <RunTimeline jobs={jobs} range={[twoHoursAgo, now]} />;
};
