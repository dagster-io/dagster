import {gql, useQuery} from '@apollo/client';
import {Box, Button, Group, Icon, stringFromValue, Tooltip} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {
  FIFTEEN_SECONDS,
  ONE_MONTH,
  QueryRefreshCountdown,
  useQueryRefreshAtInterval,
} from '../app/QueryRefresh';
import {RunStatusDot} from '../runs/RunStatusDots';
import {TerminationDialog} from '../runs/TerminationDialog';
import {RunStatus} from '../types/globalTypes';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {
  PartitionProgressQuery,
  PartitionProgressQueryVariables,
  PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill,
} from './types/PartitionProgressQuery';
interface Props {
  pipelineName: string;
  repoAddress: RepoAddress;
  backfillId: string;
}

export const PartitionProgress = (props: Props) => {
  const {pipelineName, repoAddress, backfillId} = props;
  const [shouldPoll, setShouldPoll] = React.useState(true);
  const [isTerminating, setIsTerminating] = React.useState(false);

  const queryResult = useQuery<PartitionProgressQuery, PartitionProgressQueryVariables>(
    PARTITION_PROGRESS_QUERY,
    {
      fetchPolicy: 'network-only',
      notifyOnNetworkStatusChange: true,
      variables: {
        backfillId,
      },
    },
  );

  // Technically we still poll if you disable polling on this page, just very very slowly.
  // The useQueryRefreshAtInterval hook is already complex enough, don't want to add a
  // "disabled: true" option.
  const refreshInterval = shouldPoll ? FIFTEEN_SECONDS : ONE_MONTH;
  const refreshState = useQueryRefreshAtInterval(queryResult, refreshInterval);
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
    const partitionRunStats = results.partitionRunStats;
    return {
      numQueued: partitionRunStats.numQueued,
      numInProgress: partitionRunStats.numInProgress,
      numSucceeded: partitionRunStats.numSucceeded,
      numFailed: partitionRunStats.numFailed,
      numPartitionsWithRuns: partitionRunStats.numPartitionsWithRuns,
      numTotalRuns: partitionRunStats.numTotalRuns,
    };
  }, [results]);

  React.useEffect(() => {
    if (counts) {
      const {numPartitionsWithRuns, numSucceeded, numFailed} = counts;
      setShouldPoll(numPartitionsWithRuns !== numSucceeded + numFailed);
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
    numPartitionsWithRuns,
    numTotalRuns,
  } = counts;
  const numFinished = numSucceeded + numFailed;
  const numTotal = results.partitionNames.length;
  const unscheduled = numTotal - results.numRequested;

  const skipped = results.numRequested - numPartitionsWithRuns;

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

  const unfinishedRuns = results.unfinishedRuns;
  const unfinishedMap =
    unfinishedRuns?.reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {}) || {};

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
            <Button
              outlined
              icon={<Icon name="cancel" />}
              intent="danger"
              onClick={() => setIsTerminating(true)}
            >
              Terminate
            </Button>
            <TerminationDialog
              isOpen={isTerminating}
              onClose={() => setIsTerminating(false)}
              onComplete={() => refetch()}
              selectedRuns={unfinishedMap}
            />
          </>
        ) : null}
      </Group>
      {shouldPoll && !isTerminating ? <QueryRefreshCountdown refreshState={refreshState} /> : null}
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
  query PartitionProgressQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        backfillId
        status
        numRequested
        partitionNames
        numPartitions
        partitionRunStats {
          numQueued
          numInProgress
          numSucceeded
          numFailed
          numPartitionsWithRuns
          numTotalRuns
        }
        unfinishedRuns {
          id
          canTerminate
        }
      }
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
