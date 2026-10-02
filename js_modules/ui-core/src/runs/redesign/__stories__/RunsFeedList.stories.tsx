import {MockedProvider} from '@apollo/client/testing';
import {Text} from '@dagster-io/ui-components';
import {useLocation} from 'react-router-dom';

import {
  buildAssetKey,
  buildInstigationState,
  buildInstigationTick,
  buildRun,
  buildRunStatsSnapshot,
} from '../../../graphql/builders';
import {InstigationTickStatus, InstigationType, RunStatus} from '../../../graphql/types';
import {JOB_SELECTED_TICK_QUERY} from '../../../instigation/TickDetailsDialog';
import {
  SelectedTickQuery,
  SelectedTickQueryVariables,
} from '../../../instigation/types/TickDetailsDialog.types';
import {buildQueryMock} from '../../../testing/mocking';
import {RUN_STATS_QUERY} from '../../RunStats';
import {DagsterTag} from '../../RunTag';
import {RunStatsQuery, RunStatsQueryVariables} from '../../types/RunStats.types';
import {RunsFeedList} from '../RunsFeedList';
import {backfillEntry, runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunsFeedList',
  component: RunsFeedList,
};

// Timed against the real clock so counters and relative text read as they do in the feed.
const NOW = Date.now() / 1000;
const MINUTE = 60;
const HOUR = 60 * MINUTE;

const JOB_NAME = 'daily_etl';

const salesDaily = buildAssetKey({path: ['sales', 'daily']});

const finishedAfter = (seconds: number) => ({
  creationTime: NOW - HOUR - seconds - MINUTE,
  startTime: NOW - HOUR - seconds,
  endTime: NOW - HOUR,
});

const scheduleRunWithTick = runEntry({
  id: 'a1b2c3d4-1111-2222-3333-444455556666',
  jobName: JOB_NAME,
  tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule'), tag(DagsterTag.TickId, 'tick-id')],
  assetSelectionPreview: [salesDaily, buildAssetKey({path: ['sales', 'hourly']})],
  assetSelectionCount: 2,
  ...finishedAfter(4 * MINUTE),
});

const sensorRun = runEntry({
  id: 'bbbbbbbb-1111-2222-3333-444455556666',
  runStatus: RunStatus.FAILURE,
  jobName: JOB_NAME,
  tags: [tag(DagsterTag.SensorName, 'files_sensor')],
  ...finishedAfter(2 * MINUTE + 12),
});

const liveRun = runEntry({
  id: 'cccccccc-1111-2222-3333-444455556666',
  runStatus: RunStatus.STARTED,
  jobName: JOB_NAME,
  creationTime: NOW - 3 * MINUTE,
  startTime: NOW - 2 * MINUTE,
  endTime: null,
});

const queuedRun = runEntry({
  id: 'dddddddd-1111-2222-3333-444455556666',
  runStatus: RunStatus.QUEUED,
  jobName: JOB_NAME,
  creationTime: NOW - 20,
  startTime: null,
  endTime: null,
});

const manualRun = runEntry({
  id: 'eeeeeeee-1111-2222-3333-444455556666',
  jobName: JOB_NAME,
  tags: [tag(DagsterTag.User, 'pat@example.com')],
  ...finishedAfter(35),
});

const assetBackfill = backfillEntry({
  id: 'bkfl1234',
  isAssetBackfill: true,
  user: 'pat@example.com',
  creationTime: NOW - 3 * HOUR,
  startTime: NOW - 3 * HOUR,
  endTime: NOW - HOUR,
});

const statsMockFor = (runId: string) =>
  buildQueryMock<RunStatsQuery, RunStatsQueryVariables>({
    query: RUN_STATS_QUERY,
    variables: {runId},
    data: {
      pipelineRunOrError: buildRun({
        id: runId,
        stats: buildRunStatsSnapshot({
          stepsSucceeded: 4,
          stepsFailed: 1,
          materializations: 3,
          expectations: 0,
        }),
      }),
    },
    maxUsageCount: Number.POSITIVE_INFINITY,
  });

const tickMockFor = (scheduleName: string, tickId: string) =>
  buildQueryMock<SelectedTickQuery, SelectedTickQueryVariables>({
    query: JOB_SELECTED_TICK_QUERY,
    variables: {
      instigationSelector: {
        name: scheduleName,
        repositoryName: 'my_repo',
        repositoryLocationName: 'my_location',
      },
      tickId,
    },
    data: {
      instigationStateOrError: buildInstigationState({
        id: `${scheduleName}-state-id`,
        tick: buildInstigationTick({
          id: tickId,
          tickId,
          instigationType: InstigationType.SCHEDULE,
          status: InstigationTickStatus.SUCCESS,
          timestamp: NOW - HOUR,
          requestedAssetMaterializationCount: 2,
          requestedJobRunCount: 0,
          error: null,
          skipReason: null,
        }),
      }),
    },
    maxUsageCount: Number.POSITIVE_INFINITY,
  });

const MOCKS = [
  ...[scheduleRunWithTick, sensorRun, liveRun, queuedRun, manualRun].map(({id}) =>
    statsMockFor(id),
  ),
  tickMockFor('hourly_schedule', 'tick-id'),
];

const CurrentLocation = () => {
  const {pathname} = useLocation();
  return (
    <Text color="textLight" size={12}>
      {pathname}
    </Text>
  );
};

type ListTemplateProps = {
  entries: MappedRunsFeedEntry[];
  isLoading?: boolean;
};

const ListTemplate = ({entries, isLoading = false}: ListTemplateProps) => (
  <MockedProvider mocks={MOCKS}>
    <div style={{width: 960}}>
      <CurrentLocation />
      <RunsFeedList entries={entries} isLoading={isLoading} />
    </div>
  </MockedProvider>
);

export const Loading = () => <ListTemplate entries={[]} isLoading />;

export const RowNavigation = () => (
  <ListTemplate
    entries={[liveRun, queuedRun, scheduleRunWithTick, sensorRun, manualRun, assetBackfill]}
  />
);
