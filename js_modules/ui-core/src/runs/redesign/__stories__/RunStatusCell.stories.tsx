import {MockedProvider} from '@apollo/client/testing';

import {buildRun, buildRunStatsSnapshot} from '../../../graphql/builders';
import {BulkActionStatus, RunStatus} from '../../../graphql/types';
import {buildQueryMock} from '../../../testing/mocking';
import {RUN_STATS_QUERY} from '../../RunStats';
import {RunStatsQuery, RunStatsQueryVariables} from '../../types/RunStats.types';
import {RunStatusCell} from '../RunStatusCell';
import {backfillEntry, runEntry, tag} from '../__fixtures__/RunsFeedEntries.fixtures';
import {MappedRunsFeedEntry} from '../mapRunsFeedData';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Runs Redesign/RunStatusCell',
  component: RunStatusCell,
};

// Timed against the real clock so counters and relative text read as they do in the feed.
const NOW = Date.now() / 1000;
const MINUTE = 60;
const HOUR = 60 * MINUTE;

const RUN_ID = 'status-story-run-id';

const waiting = {id: RUN_ID, creationTime: NOW - 10 * MINUTE, startTime: null, endTime: null};

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

const CellTemplate = ({entry}: {entry: MappedRunsFeedEntry}) => (
  <MockedProvider mocks={[statsMock]}>
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        width: 420,
        height: 48,
        padding: '0 16px',
        border: '1px solid var(--color-keyline-default)',
      }}
    >
      <RunStatusCell entry={entry} />
    </div>
  </MockedProvider>
);

export const Queued = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.QUEUED, ...waiting})} />
);
export const Starting = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.STARTING, ...waiting})} />
);
export const Started = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.STARTED, ...runningFor(2 * MINUTE + 14)})} />
);
export const StartedWithoutStartTime = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.STARTED, ...waiting})} />
);
export const Canceling = () => (
  <CellTemplate entry={runEntry({runStatus: RunStatus.CANCELING, ...runningFor(4 * MINUTE)})} />
);
export const Succeeded = () => (
  <CellTemplate
    entry={runEntry({runStatus: RunStatus.SUCCESS, ...finishedAfter(12 * MINUTE + 14)})}
  />
);
export const Failed = () => (
  <CellTemplate
    entry={runEntry({runStatus: RunStatus.FAILURE, ...finishedAfter(3 * MINUTE + 22)})}
  />
);
export const FailedWithQueuedRetry = () => (
  <CellTemplate
    entry={runEntry({
      runStatus: RunStatus.FAILURE,
      tags: [tag('dagster/will_retry', 'true')],
      ...finishedAfter(3 * MINUTE + 22),
    })}
  />
);
export const Canceled = () => (
  <CellTemplate
    entry={runEntry({runStatus: RunStatus.CANCELED, ...finishedAfter(4 * MINUTE + 5)})}
  />
);
export const FailingBackfill = () => (
  <CellTemplate
    entry={backfillEntry({
      runStatus: RunStatus.FAILURE,
      backfillStatus: BulkActionStatus.FAILING,
      ...runningFor(HOUR + 7 * MINUTE),
    })}
  />
);
