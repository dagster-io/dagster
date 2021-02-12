import {gql, useQuery} from '@apollo/client';
import {Button, Tooltip} from '@blueprintjs/core';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {PYTHON_ERROR_FRAGMENT} from 'src/app/PythonErrorInfo';
import {QueryCountdown} from 'src/app/QueryCountdown';
import {
  PartitionProgressQuery,
  PartitionProgressQuery_partitionBackfillOrError_PartitionBackfill,
} from 'src/partitions/types/PartitionProgressQuery';
import {RunStatusDot} from 'src/runs/RunStatusDots';
import {
  doneStatuses,
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from 'src/runs/RunStatuses';
import {TerminationDialog} from 'src/runs/TerminationDialog';
import {POLL_INTERVAL} from 'src/runs/useCursorPaginatedQuery';
import {PipelineRunStatus} from 'src/types/globalTypes';
import {Box} from 'src/ui/Box';
import {Group} from 'src/ui/Group';
import {stringFromValue} from 'src/ui/TokenizingField';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';
interface Props {
  pipelineName: string;
  repoAddress: RepoAddress;
  backfillId: string;
}

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

    const numTotalRuns = results.runs.length;
    const {numQueued, numInProgress, numSucceeded, numFailed} = results.runs.reduce(
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
    return {numQueued, numInProgress, numSucceeded, numFailed, numTotalRuns};
  }, [results]);

  React.useEffect(() => {
    if (counts) {
      const {numTotalRuns, numSucceeded, numFailed} = counts;
      setShouldPoll(numTotalRuns !== numSucceeded + numFailed);
    }
  }, [counts]);

  if (!counts || !results) {
    return <div />;
  }

  const {numQueued, numInProgress, numSucceeded, numFailed, numTotalRuns} = counts;
  const numFinished = numSucceeded + numFailed;
  const unscheduled = (results.numTotal || 0) - (results.numRequested || 0);
  const skipped = results.isPersisted ? numTotalRuns - (results.numRequested || 0) : 0;
  const numTotal = results.isPersisted ? results.numTotal || 0 : numTotalRuns;

  const table = (
    <TooltipTable>
      <tbody>
        <TooltipTableRow
          runStatus={PipelineRunStatus.QUEUED}
          humanText="Queued"
          count={numQueued}
          numTotal={numTotal}
        />
        <TooltipTableRow
          runStatus={PipelineRunStatus.STARTED}
          humanText="In progress"
          count={numInProgress}
          numTotal={numTotal}
        />
        <TooltipTableRow
          runStatus={PipelineRunStatus.SUCCESS}
          humanText="Succeeded"
          count={numSucceeded}
          numTotal={numTotal}
        />
        <TooltipTableRow
          runStatus={PipelineRunStatus.FAILURE}
          humanText="Failed"
          count={numFailed}
          numTotal={numTotal}
        />
        {results.isPersisted && numTotalRuns < (results.numRequested || 0) ? (
          <TooltipTableRow humanText="Skipped" count={skipped} numTotal={numTotal} />
        ) : null}
        {results.isPersisted ? (
          <TooltipTableRow humanText="To be scheduled" count={unscheduled} numTotal={numTotal} />
        ) : null}
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
                <Link
                  to={workspacePathFromAddress(
                    repoAddress,
                    `/pipelines/${pipelineName}/runs?${qs.stringify({
                      q: stringFromValue([{token: 'tag', value: `dagster/backfill=${backfillId}`}]),
                    })}`,
                  )}
                >
                  {numFinished}/{numTotalRuns} runs
                </Link>
                {numTotalRuns && unscheduled ? (
                  <> completed, </>
                ) : numTotalRuns ? (
                  <> completed ({((numFinished / numTotalRuns) * 100).toFixed(1)}%)</>
                ) : null}
              </div>
            ) : null}
            {unscheduled ? (
              <div style={{fontVariantNumeric: 'tabular-nums'}}>{unscheduled} to be scheduled</div>
            ) : null}
          </Group>
        </Tooltip>
        {Object.keys(unfinishedMap).length ? (
          <>
            <Button minimal icon="stop" intent="danger" onClick={() => setIsTerminating(true)}>
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
      {shouldPoll && !isTerminating ? (
        <QueryCountdown pollInterval={POLL_INTERVAL} queryResult={queryResult} />
      ) : null}
    </Box>
  );
};

const TooltipTableRow: React.FC<{
  runStatus?: PipelineRunStatus;
  humanText: string;
  count: number;
  numTotal: number;
}> = ({runStatus, humanText, count, numTotal}) => {
  if (!count) {
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
        isPersisted
        numRequested
        numTotal
        runs(limit: $limit) {
          id
          canTerminate
          status
        }
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
