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

const RUN_ID = 'status-story-run-id';

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

export const NotStarted = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.NOT_STARTED})} />
);
export const Queued = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.QUEUED})} />
);
export const Starting = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.STARTING})} />
);
export const Started = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.STARTED})} />
);
export const Managed = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.MANAGED})} />
);
export const Canceling = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.CANCELING})} />
);
export const Succeeded = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.SUCCESS})} />
);
export const Failed = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.FAILURE})} />
);
export const FailedWithQueuedRetry = () => (
  <CellTemplate
    entry={runEntry({
      id: RUN_ID,
      runStatus: RunStatus.FAILURE,
      tags: [tag('dagster/will_retry', 'true')],
    })}
  />
);
export const Canceled = () => (
  <CellTemplate entry={runEntry({id: RUN_ID, runStatus: RunStatus.CANCELED})} />
);
export const FailingBackfill = () => (
  <CellTemplate
    entry={backfillEntry({
      runStatus: RunStatus.FAILURE,
      backfillStatus: BulkActionStatus.FAILING,
    })}
  />
);
