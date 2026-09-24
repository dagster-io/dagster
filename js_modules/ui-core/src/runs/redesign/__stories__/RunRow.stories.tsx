import {MockedProvider} from '@apollo/client/testing';
import {showToast} from '@dagster-io/ui-components';

import {buildAssetKey, buildRun, buildRunStatsSnapshot} from '../../../graphql/builders';
import {RunStatus} from '../../../graphql/types';
import {buildQueryMock} from '../../../testing/mocking';
import {RUN_STATS_QUERY} from '../../RunStats';
import {DagsterTag} from '../../RunTag';
import {RunStatsQuery, RunStatsQueryVariables} from '../../types/RunStats.types';
import {RunRow} from '../RunRow';
import {backfillEntry, runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunRow',
  component: RunRow,
};

// Timed against the real clock so counters and relative text read as they do in the feed.
const NOW = Date.now() / 1000;
const MINUTE = 60;
const HOUR = 60 * MINUTE;

const RUN_ID = 'a1b2c3d4-1111-2222-3333-444455556666';
const JOB_NAME = 'daily_etl';

const runningFor = (seconds: number) => ({
  id: RUN_ID,
  creationTime: NOW - seconds - MINUTE,
  startTime: NOW - seconds,
  endTime: null,
});

const finishedAfter = (seconds: number) => ({
  id: RUN_ID,
  creationTime: NOW - HOUR - seconds - MINUTE,
  startTime: NOW - HOUR - seconds,
  endTime: NOW - HOUR,
});

const statsMock = buildQueryMock<RunStatsQuery, RunStatsQueryVariables>({
  query: RUN_STATS_QUERY,
  variables: {runId: RUN_ID},
  data: {
    pipelineRunOrError: buildRun({
      id: RUN_ID,
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

const salesDaily = buildAssetKey({path: ['sales', 'daily']});

type RowTemplateProps = {
  entry: MappedRunsFeedEntry;
  width?: number;
};

const RowTemplate = ({entry, width = 960}: RowTemplateProps) => (
  <MockedProvider mocks={[statsMock]}>
    <div style={{width, border: '1px solid var(--color-keyline-default)'}}>
      <RunRow
        entry={entry}
        onOpenTickDetails={() => {
          showToast({message: 'The tick dialog opens here.', intent: 'none'});
        }}
      />
    </div>
  </MockedProvider>
);

export const ScheduleRunWithTick = () => (
  <RowTemplate
    entry={runEntry({
      jobName: JOB_NAME,
      tags: [tag(DagsterTag.ScheduleName, 'hourly_schedule'), tag(DagsterTag.TickId, 'tick-id')],
      ...finishedAfter(4 * MINUTE + 12),
    })}
  />
);

export const ReExecutionInsideBackfill = () => (
  <RowTemplate
    entry={runEntry({
      jobName: JOB_NAME,
      parentRunId: 'pppppppp-1111-2222-3333-444455556666',
      rootRunId: 'pppppppp-1111-2222-3333-444455556666',
      tags: [tag(DagsterTag.Backfill, 'bkfl1234'), tag(DagsterTag.User, 'pat@example.com')],
      ...finishedAfter(6 * MINUTE),
    })}
  />
);

export const LiveRun = () => (
  <RowTemplate
    entry={runEntry({
      runStatus: RunStatus.STARTED,
      jobName: JOB_NAME,
      assetSelectionPreview: [salesDaily],
      assetSelectionCount: 1,
      ...runningFor(2 * MINUTE + 14),
    })}
  />
);

export const AssetBackfill = () => (
  <RowTemplate
    entry={backfillEntry({
      id: 'bkfl1234',
      isAssetBackfill: true,
      user: 'pat@example.com',
      creationTime: NOW - 3 * HOUR,
      startTime: NOW - 3 * HOUR,
      endTime: NOW - HOUR,
    })}
  />
);

export const Narrow = () => (
  <RowTemplate
    width={480}
    entry={runEntry({
      jobName: JOB_NAME,
      tags: [
        tag(DagsterTag.ScheduleName, 'hourly_ingestion_schedule_for_the_warehouse_tables'),
        tag(DagsterTag.TickId, 'tick-id'),
      ],
      assetSelectionPreview: [salesDaily],
      assetSelectionCount: 1,
      ...finishedAfter(5 * MINUTE),
    })}
  />
);
