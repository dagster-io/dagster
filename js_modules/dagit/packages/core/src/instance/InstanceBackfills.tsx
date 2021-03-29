import {gql, QueryResult} from '@apollo/client';
import {Colors, Icon, NonIdealState, Popover, Button, Menu, MenuItem, Tag} from '@blueprintjs/core';
import qs from 'qs';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {PipelineReference} from '../pipelines/PipelineReference';
import {
  doneStatuses,
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../runs/RunStatuses';
import {TerminationDialog} from '../runs/TerminationDialog';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {BulkActionStatus, PipelineRunStatus} from '../types/globalTypes';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {CursorPaginationControls} from '../ui/CursorControls';
import {Group} from '../ui/Group';
import {Loading} from '../ui/Loading';
import {Table} from '../ui/Table';
import {stringFromValue} from '../ui/TokenizingField';
import {FontFamily} from '../ui/styles';
import {workspacePath} from '../workspace/workspacePath';

import {BackfillTerminationDialog} from './BackfillTerminationDialog';
import {
  InstanceBackfillsQuery,
  InstanceBackfillsQueryVariables,
  InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results,
} from './types/InstanceBackfillsQuery';
import {InstanceHealthQuery} from './types/InstanceHealthQuery';

type Backfill = InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results;

const PAGE_SIZE = 25;

export const InstanceBackfills = ({queryData}: {queryData: QueryResult<InstanceHealthQuery>}) => {
  const {queryResult, paginationProps} = useCursorPaginatedQuery<
    InstanceBackfillsQuery,
    InstanceBackfillsQueryVariables
  >({
    query: BACKFILLS_QUERY,
    variables: {},
    pageSize: PAGE_SIZE,
    nextCursorForResult: (result) =>
      result.partitionBackfillsOrError.__typename === 'PartitionBackfills'
        ? result.partitionBackfillsOrError.results[PAGE_SIZE - 1]?.backfillId
        : undefined,
    getResultArray: (result) =>
      result?.partitionBackfillsOrError.__typename === 'PartitionBackfills'
        ? result.partitionBackfillsOrError.results
        : [],
  });

  return (
    <Loading queryResult={queryResult} allowStaleData={true}>
      {({partitionBackfillsOrError}) => {
        if (partitionBackfillsOrError.__typename === 'PythonError') {
          return <PythonErrorInfo error={partitionBackfillsOrError} />;
        }

        if (!partitionBackfillsOrError.results.length) {
          return (
            <NonIdealState
              icon="multi-select"
              title="No backfills found"
              description={<p>This instance does not have any backfill jobs.</p>}
            />
          );
        }

        const daemonHealths = queryData.data?.instance.daemonHealth.allDaemonStatuses || [];
        const backfillHealths = daemonHealths
          .filter((daemon) => daemon.daemonType == 'BACKFILL')
          .map((daemon) => daemon.required && daemon.healthy);
        const isBackfillHealthy = backfillHealths.length && backfillHealths.every((x) => x);

        return (
          <>
            {isBackfillHealthy ? null : (
              <Box margin={{bottom: 8}}>
                <Alert
                  intent="warning"
                  title="The backfill daemon is not running."
                  description={
                    <div>
                      See the{' '}
                      <a
                        href="https://docs.dagster.io/overview/daemon"
                        target="_blank"
                        rel="noreferrer"
                      >
                        dagster-daemon documentation
                      </a>{' '}
                      for more information on how to deploy the dagster-daemon process.
                    </div>
                  }
                />
              </Box>
            )}
            <BackfillTable
              backfills={partitionBackfillsOrError.results.slice(0, PAGE_SIZE)}
              refetch={queryResult.refetch}
            />
            {partitionBackfillsOrError.results.length > 0 ? (
              <div style={{marginTop: '16px'}}>
                <CursorPaginationControls {...paginationProps} />
              </div>
            ) : null}
          </>
        );
      }}
    </Loading>
  );
};

const BackfillTable = ({backfills, refetch}: {backfills: Backfill[]; refetch: () => void}) => {
  const [terminationBackfill, setTerminationBackfill] = React.useState<Backfill>();
  const [cancelRunBackfill, setCancelRunBackfill] = React.useState<Backfill>();

  const candidateId = terminationBackfill?.backfillId;
  React.useEffect(() => {
    if (candidateId) {
      const [backfill] = backfills.filter((backfill) => backfill.backfillId === candidateId);
      setTerminationBackfill(backfill);
    }
  }, [backfills, candidateId]);
  const cancelableRuns = cancelRunBackfill?.runs.filter(
    (run) => !doneStatuses.has(run?.status) && run.canTerminate,
  );
  const unfinishedMap =
    cancelRunBackfill?.runs
      .filter((run) => !doneStatuses.has(run?.status))
      .reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {}) || {};

  return (
    <>
      <Table>
        <thead>
          <tr>
            <th style={{width: '120px'}}>Backfill Id</th>
            <th>Partition Set</th>
            <th style={{textAlign: 'right'}}>Progress</th>
            <th>Status</th>
            <th>Created</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {backfills.map((backfill: Backfill) => (
            <BackfillRow
              key={backfill.backfillId}
              backfill={backfill}
              onTerminateBackfill={setTerminationBackfill}
            />
          ))}
        </tbody>
      </Table>
      <BackfillTerminationDialog
        backfill={terminationBackfill}
        onClose={() => setTerminationBackfill(undefined)}
        onComplete={() => refetch()}
      />
      <TerminationDialog
        isOpen={!!cancelableRuns?.length}
        onClose={() => setCancelRunBackfill(undefined)}
        onComplete={() => refetch()}
        selectedRuns={unfinishedMap}
      />
    </>
  );
};

const BackfillRow = ({
  backfill,
  onTerminateBackfill,
}: {
  backfill: Backfill;
  onTerminateBackfill: (backfill: Backfill) => void;
}) => {
  const counts = React.useMemo(() => getProgressCounts(backfill), [backfill]);
  const runsUrl = `/instance/runs?${qs.stringify({
    q: stringFromValue([{token: 'tag', value: `dagster/backfill=${backfill.backfillId}`}]),
  })}`;

  const partitionSetBackfillUrl = backfill.partitionSet
    ? workspacePath(
        backfill.partitionSet.repositoryOrigin.repositoryName,
        backfill.partitionSet.repositoryOrigin.repositoryLocationName,
        `/pipelines/${backfill.partitionSet.pipelineName}/partitions?${qs.stringify({
          partitionSet: backfill.partitionSet.name,
          q: stringFromValue([{token: 'tag', value: `dagster/backfill=${backfill.backfillId}`}]),
        })}`,
      )
    : null;

  const canCancel = backfill.runs.some((run) => run.canTerminate);

  return (
    <tr>
      <td style={{width: '120px', fontFamily: FontFamily.monospace}}>
        {partitionSetBackfillUrl ? (
          <Link to={partitionSetBackfillUrl}>{backfill.backfillId}</Link>
        ) : (
          backfill.backfillId
        )}
      </td>
      <td>
        {backfill.partitionSet ? (
          <Group direction={'column'} spacing={8}>
            <Link
              to={workspacePath(
                backfill.partitionSet.repositoryOrigin.repositoryName,
                backfill.partitionSet.repositoryOrigin.repositoryLocationName,
                `/pipelines/${
                  backfill.partitionSet.pipelineName
                }/partitions?partitionSet=${encodeURIComponent(backfill.partitionSet.name)}`,
              )}
            >
              {backfill.partitionSet.name}
            </Link>
            <span style={{color: Colors.DARK_GRAY3, fontSize: 12}}>
              {backfill.partitionSet.repositoryOrigin.repositoryName}@
              {backfill.partitionSet.repositoryOrigin.repositoryLocationName}
            </span>
            <Group direction="row" spacing={4} alignItems="center">
              <Icon
                icon="diagram-tree"
                color={Colors.GRAY2}
                iconSize={9}
                style={{position: 'relative', top: '-3px'}}
              />
              <span style={{fontSize: '13px'}}>
                <PipelineReference
                  pipelineName={backfill.partitionSet.pipelineName}
                  pipelineHrefContext={{
                    name: backfill.partitionSet.repositoryOrigin.repositoryName,
                    location: backfill.partitionSet.repositoryOrigin.repositoryLocationName,
                  }}
                  mode={backfill.partitionSet.mode}
                />
              </span>
            </Group>
          </Group>
        ) : (
          backfill.partitionSetName
        )}
      </td>
      <td style={{textAlign: 'right'}}>
        <BackfillProgress backfill={backfill} />
      </td>
      <td>
        {backfill.status === BulkActionStatus.CANCELED ? (
          <Box margin={{bottom: 12}}>
            <Tag minimal intent="danger">
              CANCELED
            </Tag>
          </Box>
        ) : null}
        <BackfillStatusTable backfill={backfill} />
      </td>
      <td>{backfill.timestamp ? <TimestampDisplay timestamp={backfill.timestamp} /> : '-'}</td>
      <td style={{width: '100px'}}>
        <Popover
          content={
            <Menu>
              {counts.numUnscheduled && backfill.status === BulkActionStatus.REQUESTED ? (
                <MenuItem
                  text="Cancel backfill submission"
                  icon="stop"
                  intent="danger"
                  onClick={() => onTerminateBackfill(backfill)}
                />
              ) : null}
              {canCancel ? (
                <MenuItem
                  text="Terminate unfinished runs"
                  icon="stop"
                  intent="danger"
                  onClick={() => onTerminateBackfill(backfill)}
                />
              ) : null}
              {partitionSetBackfillUrl ? (
                <MenuItem
                  text="View Partition Matrix"
                  icon="multi-select"
                  href={partitionSetBackfillUrl}
                />
              ) : null}
              <MenuItem text="View Backfill Runs" icon="history" href={runsUrl} />
            </Menu>
          }
          position="bottom"
        >
          <Button small minimal icon="chevron-down" style={{marginLeft: '4px'}} />
        </Popover>
      </td>
    </tr>
  );
};

const getProgressCounts = (backfill: Backfill) => {
  const numTotalRuns = backfill.runs.length;
  const {numQueued, numInProgress, numSucceeded, numFailed} = backfill.runs.reduce(
    (accum: any, {status}: {status: PipelineRunStatus}) => {
      return {
        numQueued: accum.numQueued + (queuedStatuses.has(status) ? 1 : 0),
        numInProgress: accum.numInProgress + (inProgressStatuses.has(status) ? 1 : 0),
        numSucceeded: accum.numSucceeded + (successStatuses.has(status) ? 1 : 0),
        numFailed: accum.numFailed + (failedStatuses.has(status) ? 1 : 0),
      };
    },
    {numQueued: 0, numInProgress: 0, numSucceeded: 0, numFailed: 0},
  );
  const numTotal = numTotalRuns > backfill.numTotal ? numTotalRuns : backfill.numTotal;

  return {
    numQueued,
    numInProgress,
    numSucceeded,
    numFailed,
    numUnscheduled: (backfill.numTotal || 0) - (backfill.numRequested || 0),
    numSkipped: (backfill.numRequested || 0) - numTotalRuns,
    numTotal,
  };
};

const BackfillProgress = ({backfill}: {backfill: Backfill}) => {
  const {numSucceeded, numFailed, numSkipped, numTotal} = React.useMemo(
    () => getProgressCounts(backfill),
    [backfill],
  );
  const numCompleted = numSucceeded + numSkipped + numFailed;
  return (
    <span
      style={{
        fontSize: 36,
        fontWeight: 'bold',
        color: Colors.GRAY1,
        fontVariantNumeric: 'tabular-nums',
      }}
    >
      {numTotal ? Math.floor((100 * numCompleted) / numTotal) : '-'}%
    </span>
  );
};

const BackfillStatusTable = ({backfill}: {backfill: Backfill}) => {
  const {
    numQueued,
    numInProgress,
    numSucceeded,
    numFailed,
    numSkipped,
    numUnscheduled,
    numTotal,
  } = React.useMemo(() => getProgressCounts(backfill), [backfill]);

  return (
    <Table style={{marginRight: 20, maxWidth: 250}}>
      <tbody>
        <BackfillStatusTableRow label="Queued" count={numQueued} />
        <BackfillStatusTableRow label="In progress" count={numInProgress} />
        <BackfillStatusTableRow label="Succeeded" count={numSucceeded} />
        <BackfillStatusTableRow label="Failed" count={numFailed} />
        <BackfillStatusTableRow label="Skipped" count={numSkipped} />
        {backfill.status === BulkActionStatus.CANCELED ? (
          <BackfillStatusTableRow label="Unscheduled" count={numUnscheduled} />
        ) : (
          <BackfillStatusTableRow label="To be scheduled" count={numUnscheduled} />
        )}
        <BackfillStatusTableRow label="Total" count={numTotal} isTotal={true} />
      </tbody>
    </Table>
  );
};

const BackfillStatusTableRow = ({
  label,
  count,
  isTotal,
}: {
  label: string;
  count: number;
  isTotal?: boolean;
}) => {
  if (!count || count < 0) {
    return null;
  }
  return (
    <tr
      style={{
        boxShadow: 'none',
        fontVariant: 'tabular-nums',
      }}
    >
      <td
        style={{
          borderTop: isTotal ? `1px solid ${Colors.LIGHT_GRAY1}` : undefined,
          maxWidth: '100px',
          padding: '3px 5px',
        }}
      >
        <Group direction="row" spacing={8} alignItems="center">
          <div>{label}</div>
        </Group>
      </td>
      <td
        style={{
          borderTop: isTotal ? `1px solid ${Colors.LIGHT_GRAY1}` : undefined,
          maxWidth: '50px',
          padding: '3px 5px',
        }}
      >
        <Box flex={{justifyContent: 'flex-end'}}>{count}</Box>
      </td>
    </tr>
  );
};

const BACKFILLS_QUERY = gql`
  query InstanceBackfillsQuery($cursor: String, $limit: Int) {
    partitionBackfillsOrError(cursor: $cursor, limit: $limit) {
      ... on PartitionBackfills {
        results {
          backfillId
          status
          numRequested
          numTotal
          runs(limit: $limit) {
            id
            canTerminate
            status
          }
          timestamp
          partitionSetName
          partitionSet {
            id
            name
            mode
            pipelineName
            repositoryOrigin {
              id
              repositoryName
              repositoryLocationName
            }
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;
