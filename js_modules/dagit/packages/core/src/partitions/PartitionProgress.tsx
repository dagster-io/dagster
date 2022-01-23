import {gql, useQuery} from '@apollo/client';
import {Box, ButtonWIP, Group, IconWIP, stringFromValue, Tooltip} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {QueryCountdown} from '../app/QueryCountdown';
import {RunStatusDot} from '../runs/RunStatusDots';
import {
  doneStatuses,
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../runs/RunStatuses';
import {DagsterTag} from '../runs/RunTag';
import {TerminationDialog} from '../runs/TerminationDialog';
import {POLL_INTERVAL} from '../runs/useCursorPaginatedQuery';
import {RunStatus} from '../types/globalTypes';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {
  PartitionProgressQuery,
  PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill,
  PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_runs,
} from './types/PartitionProgressQuery';
interface Props {
  pipelineName: string;
  repoAddress: RepoAddress;
  backfillId: string;
}

type BackfillRun = PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill_runs;

export const PartitionProgress = (props: Props) => {
  const {pipelineName, repoAddress, backfillId} = props;
  const [shouldPoll, setShouldPoll] = React.useState(true);
  const [isTerminating, setIsTerminating] = React.useState(false);

  const queryResult = useQuery<PartitionProgressQuery>(PARTITION_PROGRESS_QUERY, {
    fetchPolicy: 'network-only',
    pollInterval: shouldPoll ? POLL_INTERVAL : undefined,
    notifyOnNetworkStatusChange: true,
    variables: {
      backfillId,
      limit: 100000,
    },
  });

  const {data, refetch} = queryResult;

  const results: PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill | null = React.useMemo(() => {
    if (!data || !data?.partitionBackfillOrError) {
      return null;
    }

    if (data.partitionBackfillOrError.__typename === 'PythonError') {
      return null;
    }

    return data.partitionBackfillOrError;
  }, [data]);

  const counts = React.useMemo(() => {
    if (!results) {
      return null;
    }
    const byPartitionRuns: {[key: string]: BackfillRun} = {};
    results.runs.forEach((run) => {
      const [runPartitionName] = run.tags
        .filter((tag) => tag.key === DagsterTag.Partition)
        .map((tag) => tag.value);

      if (runPartitionName && !byPartitionRuns[runPartitionName]) {
        byPartitionRuns[runPartitionName] = run;
      }
    });

    const latestPartitionRuns = Object.values(byPartitionRuns);

    const {numQueued, numInProgress, numSucceeded, numFailed} = latestPartitionRuns.reduce(
      (accum, {status}) => {
        return {
          numQueued: accum.numQueued + (queuedStatuses.has(status) ? 1 : 0),
          numInProgress: accum.numInProgress + (inProgressStatuses.has(status) ? 1 : 0),
          numSucceeded: accum.numSucceeded + (successStatuses.has(status) ? 1 : 0),
          numFailed: accum.numFailed + (failedStatuses.has(status) ? 1 : 0),
        };
      },
      {numQueued: 0, numInProgress: 0, numSucceeded: 0, numFailed: 0},
    );
    return {
      numQueued,
      numInProgress,
      numSucceeded,
      numFailed,
      numPartitionRuns: latestPartitionRuns.length,
      numTotalRuns: results.runs.length,
    };
  }, [results]);

  React.useEffect(() => {
    if (counts) {
      const {numPartitionRuns, numSucceeded, numFailed} = counts;
      setShouldPoll(numPartitionRuns !== numSucceeded + numFailed);
    }
  }, [counts]);

  if (!counts || !results) {
    return <div />;
  }

  const {
    numQueued,
    numInProgress,
    numSucceeded,
    numFailed,
    numPartitionRuns,
    numTotalRuns,
  } = counts;
  const numFinished = numSucceeded + numFailed;
  const unscheduled = results.numTotal - results.numRequested;

  const skipped = results.numRequested - numPartitionRuns;
  const numTotal = results.numTotal;

  const table = (
    <TooltipTable>
      <tbody>
        <TooltipTableRow
          runStatus={RunStatus.QUEUED}
          humanText="Queued"
          count={numQueued}
          numTotal={numTotal}
        />
        <TooltipTableRow
          runStatus={RunStatus.STARTED}
          humanText="In progress"
          count={numInProgress}
          numTotal={numTotal}
        />
        <TooltipTableRow
          runStatus={RunStatus.SUCCESS}
          humanText="Succeeded"
          count={numSucceeded}
          numTotal={numTotal}
        />
        <TooltipTableRow
          runStatus={RunStatus.FAILURE}
          humanText="Failed"
          count={numFailed}
          numTotal={numTotal}
        />
        {skipped > 0 ? (
          <TooltipTableRow humanText="Skipped" count={skipped} numTotal={numTotal} />
        ) : null}
        <TooltipTableRow humanText="To be scheduled" count={unscheduled} numTotal={numTotal} />
      </tbody>
    </TooltipTable>
  );

  const unfinishedMap: {[id: string]: boolean} = results.runs
    .filter((run) => !doneStatuses.has(run?.status))
    .reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {});

  return (
    <Box flex={{alignItems: 'center', grow: 1, justifyContent: 'space-between'}}>
      <Group direction="row" spacing={8} alignItems="center">
        <Tooltip content={table}>
          <Group direction="row" spacing={8} alignItems="center">
            {numTotalRuns ? (
              <div style={{fontVariantNumeric: 'tabular-nums'}}>
                <Link to="/instance/backfills">
                  {numFinished} / {numTotal}
                </Link>
                <span> partitions completed</span>
                {numTotalRuns ? (
                  <span>
                    {' '}
                    (
                    <Link
                      to={workspacePathFromAddress(
                        repoAddress,
                        `/pipeline_or_job/${pipelineName}/runs?${qs.stringify({
                          q: [
                            stringFromValue([
                              {token: 'tag', value: `dagster/backfill=${backfillId}`},
                            ]),
                          ],
                        })}`,
                      )}
                    >
                      {numTotalRuns} runs
                    </Link>
                    )
                  </span>
                ) : null}
                {unscheduled ? <span>, </span> : null}
              </div>
            ) : null}
            {unscheduled ? (
              <Link to="/instance/backfills">
                <div style={{fontVariantNumeric: 'tabular-nums'}}>
                  {unscheduled} to be scheduled
                </div>
              </Link>
            ) : null}
          </Group>
        </Tooltip>
        {Object.keys(unfinishedMap).length ? (
          <>
            <ButtonWIP
              outlined
              icon={<IconWIP name="cancel" />}
              intent="danger"
              onClick={() => setIsTerminating(true)}
            >
              Terminate
            </ButtonWIP>
            <TerminationDialog
              isOpen={isTerminating}
              onClose={() => setIsTerminating(false)}
              onComplete={() => refetch()}
              selectedRuns={unfinishedMap}
            />
          </>
        ) : null}
      </Group>
      {shouldPoll && !isTerminating ? (
        <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
      ) : null}
    </Box>
  );
};

const TooltipTableRow: React.FC<{
  runStatus?: RunStatus;
  humanText: string;
  count: number;
  numTotal: number;
}> = ({runStatus, humanText, count, numTotal}) => {
  if (!count || count < 0) {
    return null;
  }

  return (
    <tr>
      <td>
        <Group direction="row" spacing={8} alignItems="center">
          {runStatus ? <RunStatusDot status={runStatus} size={10} /> : null}
          <div>{humanText}</div>
        </Group>
      </td>
      <td>
        {count}/{numTotal}
      </td>
    </tr>
  );
};

const TooltipTable = styled.table`
  border-spacing: 0;
  td {
    font-variant-numeric: tabular-nums;
  }
  td:first-child {
    width: 120px;
  }
  td:last-child {
    text-align: right;
  }
`;

const PARTITION_PROGRESS_QUERY = gql`
  query PartitionProgressQuery($backfillId: String!, $limit: Int) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        backfillId
        status
        numRequested
        numTotal
        runs(limit: $limit) {
          id
          canTerminate
          status
          tags {
            key
            value
          }
        }
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
