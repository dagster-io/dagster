import {Meta} from '@storybook/react';
import faker from 'faker';
import {useMemo} from 'react';

import {RunStatus} from '../../graphql/types';
import {RunTimeline} from '../../runs/RunTimeline';
import {generateRunMocks} from '../../testing/generateRunMocks';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {TimelineRow} from '../RunTimelineTypes';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'RunTimeline',
  component: RunTimeline,
} as Meta;

const makeRepoAddress = () =>
  buildRepoAddress(faker.random.words(1).toLowerCase(), faker.random.words(1).toLowerCase());

export const OneRow = () => {
  const sixHoursAgo = useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = useMemo(() => Date.now(), []);

  const rows: TimelineRow[] = useMemo(() => {
    const rowKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: rowKey,
        name: rowKey,
        type: 'job',
        path: `/${rowKey}`,
        repoAddress,
        runs: generateRunMocks(6, [sixHoursAgo, now]),
      },
    ];
  }, [sixHoursAgo, now]);

  return <RunTimeline rows={rows} rangeMs={[sixHoursAgo, now]} />;
};

export const RowWithOverlappingRuns = () => {
  const sixHoursAgo = useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = useMemo(() => Date.now(), []);

  const rows: TimelineRow[] = useMemo(() => {
    const rowKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    const [first, second, third] = generateRunMocks(3, [sixHoursAgo, now]);
    return [
      {
        key: rowKey,
        name: rowKey,
        type: 'job',
        path: `/${rowKey}`,
        repoAddress,
        runs: [{...first!}, {...first!}, {...second!}, {...second!}, {...second!}, third!],
      },
    ];
  }, [sixHoursAgo, now]);

  return <RunTimeline rows={rows} rangeMs={[sixHoursAgo, now]} />;
};

export const OverlapWithRunning = () => {
  const twoHoursAgo = useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
  const now = useMemo(() => Date.now(), []);

  const rows: TimelineRow[] = useMemo(() => {
    const rowKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: rowKey,
        name: rowKey,
        type: 'job',
        path: `/${rowKey}`,
        repoAddress,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 20 * 60 * 1000,
            endTime: twoHoursAgo + 95 * 60 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 90 * 60 * 1000,
            endTime: twoHoursAgo + 110 * 60 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.STARTED,
            startTime: twoHoursAgo + 60 * 60 * 1000,
            endTime: now,
            automation: null,
          },
        ],
      },
    ];
  }, [twoHoursAgo, now]);

  return <RunTimeline rows={rows} rangeMs={[twoHoursAgo, now + 60 * 6000]} />;
};

export const ManyRows = () => {
  const sixHoursAgo = useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = useMemo(() => Date.now(), []);

  const rows: TimelineRow[] = useMemo(() => {
    const repoAddress = makeRepoAddress();
    return [...new Array(12)].reduce((accum) => {
      const rowKey = faker.random.words(3).split(' ').join('-').toLowerCase();
      return [
        ...accum,
        {
          key: rowKey,
          name: rowKey,
          path: `/${rowKey}`,
          type: 'job',
          repoAddress,
          runs: generateRunMocks(6, [sixHoursAgo, now]),
        },
      ];
    }, []);
  }, [sixHoursAgo, now]);

  return <RunTimeline rows={rows} rangeMs={[sixHoursAgo, now]} />;
};

export const VeryLongRunning = () => {
  const fourHoursAgo = useMemo(() => Date.now() - 4 * 60 * 60 * 1000, []);
  const sixHoursAgo = useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
  const twoDaysAgo = useMemo(() => Date.now() - 48 * 60 * 60 * 1000, []);
  const future = useMemo(() => Date.now() + 1 * 60 * 60 * 1000, []);

  const rows: TimelineRow[] = useMemo(() => {
    const repoAddress = makeRepoAddress();
    const rowKeyA = faker.random.words(2).split(' ').join('-').toLowerCase();
    const rowKeyB = faker.random.words(2).split(' ').join('-').toLowerCase();
    return [
      {
        key: rowKeyA,
        name: rowKeyA,
        type: 'job',
        path: `/${rowKeyA}`,
        repoAddress,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: RunStatus.FAILURE,
            startTime: twoDaysAgo,
            endTime: sixHoursAgo,
            automation: null,
          },
        ],
      },
      {
        key: rowKeyB,
        name: rowKeyB,
        type: 'job',
        path: `/${rowKeyB}`,
        repoAddress,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: RunStatus.STARTED,
            startTime: twoDaysAgo,
            endTime: Date.now(),
            automation: null,
          },
        ],
      },
    ];
  }, [twoDaysAgo, sixHoursAgo]);

  return <RunTimeline rows={rows} rangeMs={[fourHoursAgo, future]} />;
};

export const MultipleStatusesBatched = () => {
  const twoHoursAgo = useMemo(() => Date.now() - 2 * 60 * 60 * 1000, []);
  const now = useMemo(() => Date.now(), []);

  const rows: TimelineRow[] = useMemo(() => {
    const rowKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: rowKey,
        name: rowKey,
        type: 'job',
        path: `/${rowKey}`,
        repoAddress,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 20 * 60 * 1000,
            endTime: twoHoursAgo + 95 * 60 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 90 * 60 * 1000,
            endTime: twoHoursAgo + 110 * 60 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.FAILURE,
            startTime: twoHoursAgo + 60 * 60 * 1000,
            endTime: now,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: twoHoursAgo + 60 * 60 * 1000,
            endTime: now,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.STARTED,
            startTime: twoHoursAgo + 60 * 60 * 1000,
            endTime: now,
            automation: null,
          },
        ],
      },
    ];
  }, [twoHoursAgo, now]);

  return <RunTimeline rows={rows} rangeMs={[twoHoursAgo, now]} />;
};

export const BatchThresholdTesting = () => {
  const threeHoursAgo = useMemo(() => Date.now() - 3 * 60 * 60 * 1000, []);
  const now = useMemo(() => Date.now(), []);

  const rows: TimelineRow[] = useMemo(() => {
    const rowKey = faker.random.words(2).split(' ').join('-').toLowerCase();
    const repoAddress = makeRepoAddress();
    return [
      {
        key: rowKey,
        name: rowKey,
        type: 'job',
        path: `/${rowKey}`,
        repoAddress,
        runs: [
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now,
            endTime: now + 5 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 2 * 1000,
            endTime: now + 60 * 2 * 1000 + 5 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 4 * 1000,
            endTime: now + 60 * 4 * 1000 + 5 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 6 * 1000,
            endTime: now + 60 * 6 * 1000 + 5 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: 'SCHEDULED',
            startTime: now + 60 * 8 * 1000,
            endTime: now + 60 * 8 * 1000 + 5 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.SUCCESS,
            startTime: threeHoursAgo + 24 * 60 * 1000,
            endTime: threeHoursAgo + 26 * 60 * 1000,
            automation: null,
          },
          {
            id: faker.datatype.uuid(),
            status: RunStatus.FAILURE,
            startTime: threeHoursAgo + 28 * 60 * 1000,
            endTime: threeHoursAgo + 30 * 60 * 1000,
            automation: null,
          },
        ],
      },
    ];
  }, [threeHoursAgo, now]);

  return <RunTimeline rows={rows} rangeMs={[threeHoursAgo, now + 60 * 60 * 1000]} />;
};

export const GroupByAutomations = () => {
  const sixHoursAgo = useMemo(() => Date.now() - 6 * 60 * 60 * 1000, []);
  const now = useMemo(() => Date.now(), []);

  const rows: TimelineRow[] = useMemo(() => {
    const repoAddress = makeRepoAddress();
    const automations = [...new Array(12)].reduce((accum, _, ii) => {
      const rowKey = faker.random.words(3).split(' ').join('-').toLowerCase();
      const rowType = ii % 2 ? 'schedule' : 'sensor';
      const pathPrefix = rowType === 'schedule' ? 'schedules' : 'sensors';
      return [
        ...accum,
        {
          key: rowKey,
          name: rowKey,
          path: `/${pathPrefix}/${rowKey}`,
          type: rowType,
          repoAddress,
          runs: generateRunMocks(6, [sixHoursAgo, now]),
        },
      ];
    }, []);
    return [
      ...automations,
      {
        key: 'manual',
        name: 'Launched manually',
        path: null,
        type: 'manual',
        repoAddress,
        runs: generateRunMocks(6, [sixHoursAgo, now]),
      },
    ];
  }, [sixHoursAgo, now]);

  return <RunTimeline rows={rows} rangeMs={[sixHoursAgo, now]} />;
};
