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
  PartitionProgressQuery_pipelineRunsOrError_PipelineRuns_results,
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
import {stringFromValue, TokenizingFieldValue} from 'src/ui/TokenizingField';
import {RepoAddress} from 'src/workspace/types';
import {workspacePathFromAddress} from 'src/workspace/workspacePath';
interface Props {
  pipelineName: string;
  repoAddress: RepoAddress;
  runTags: TokenizingFieldValue[];
}

export const PartitionProgress = (props: Props) => {
  const {pipelineName, repoAddress, runTags} = props;
  const tags = runTags.map((token) => {
    const [key, value] = token.value.split('=');
    return {key, value};
  });
  const [shouldPoll, setShouldPoll] = React.useState(true);
  const [isTerminating, setIsTerminating] = React.useState(false);

  const queryResult = useQuery<PartitionProgressQuery>(PARTITION_PROGRESS_QUERY, {
    fetchPolicy: 'network-only',
    pollInterval: shouldPoll ? POLL_INTERVAL : undefined,
    notifyOnNetworkStatusChange: true,
    variables: {
      filter: {pipelineName, tags},
      limit: 100000,
    },
  });

  const {data, refetch} = queryResult;

  const results:
    | PartitionProgressQuery_pipelineRunsOrError_PipelineRuns_results[]
    | null = React.useMemo(() => {
    if (!data || !data?.pipelineRunsOrError) {
      return null;
    }

    const runs = data.pipelineRunsOrError;
    if (runs.__typename === 'InvalidPipelineRunsFilterError' || runs.__typename === 'PythonError') {
      return null;
    }

    return runs.results;
  }, [data]);

  const counts = React.useMemo(() => {
    if (!results) {
      return null;
    }

    const total = results.length;
    const {queued, inProgress, succeeded, failed} = results.reduce(
      (accum, {status}) => {
        return {
          queued: accum.queued + (queuedStatuses.has(status) ? 1 : 0),
          inProgress: accum.inProgress + (inProgressStatuses.has(status) ? 1 : 0),
          succeeded: accum.succeeded + (successStatuses.has(status) ? 1 : 0),
          failed: accum.failed + (failedStatuses.has(status) ? 1 : 0),
        };
      },
      {queued: 0, inProgress: 0, succeeded: 0, failed: 0},
    );
    return {queued, inProgress, succeeded, failed, total};
  }, [results]);

  React.useEffect(() => {
    if (counts) {
      const {total, succeeded, failed} = counts;
      setShouldPoll(total !== succeeded + failed);
    }
  }, [counts]);

  if (!counts || !results) {
    return <div />;
  }

  const {queued, inProgress, succeeded, failed, total} = counts;
  const finished = succeeded + failed;

  const table = (
    <TooltipTable>
      <tbody>
        <TooltipTableRow
          runStatus={PipelineRunStatus.QUEUED}
          humanText="Queued"
          count={queued}
          total={total}
        />
        <TooltipTableRow
          runStatus={PipelineRunStatus.STARTED}
          humanText="In progress"
          count={inProgress}
          total={total}
        />
        <TooltipTableRow
          runStatus={PipelineRunStatus.SUCCESS}
          humanText="Succeeded"
          count={succeeded}
          total={total}
        />
        <TooltipTableRow
          runStatus={PipelineRunStatus.FAILURE}
          humanText="Failed"
          count={failed}
          total={total}
        />
      </tbody>
    </TooltipTable>
  );

  const unfinishedMap: {[id: string]: boolean} = results
    .filter((run) => !doneStatuses.has(run?.status))
    .reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {});

  return (
    <Box flex={{alignItems: 'center', grow: 1, justifyContent: 'space-between'}}>
      <Group direction="row" spacing={8} alignItems="center">
        <div style={{fontVariantNumeric: 'tabular-nums'}}>
          <Tooltip content={table}>
            <Link
              to={workspacePathFromAddress(
                repoAddress,
                `/pipelines/${pipelineName}/runs?${qs.stringify({q: stringFromValue(runTags)})}`,
              )}
            >
              {finished}/{total} runs
            </Link>
          </Tooltip>{' '}
          done ({((finished / total) * 100).toFixed(1)}%)
        </div>
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
  runStatus: PipelineRunStatus;
  humanText: string;
  count: number;
  total: number;
}> = ({runStatus, humanText, count, total}) => {
  if (!count) {
    return null;
  }

  return (
    <tr>
      <td>
        <Group direction="row" spacing={8} alignItems="center">
          <RunStatusDot status={runStatus} size={10} />
          <div>{humanText}</div>
        </Group>
      </td>
      <td>
        {count}/{total}
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
  query PartitionProgressQuery($filter: PipelineRunsFilter!, $limit: Int) {
    pipelineRunsOrError(filter: $filter, limit: $limit) {
      ... on PipelineRuns {
        results {
          id
          canTerminate
          status
        }
      }
      ... on InvalidPipelineRunsFilterError {
        message
      }
      ... on PythonError {
        ...PythonErrorFragment
      }
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
