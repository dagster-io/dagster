import {gql, useQuery, useMutation} from '@apollo/client';
import qs from 'qs';
import * as React from 'react';
import {useHistory, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {usePermissions} from '../app/Permissions';
import {PythonErrorInfo, PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorInfo';
import {useDocumentTitle} from '../hooks/useDocumentTitle';
import {PipelineReference} from '../pipelines/PipelineReference';
import {
  doneStatuses,
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../runs/RunStatuses';
import {DagsterTag} from '../runs/RunTag';
import {TerminationDialog} from '../runs/TerminationDialog';
import {useCursorPaginatedQuery} from '../runs/useCursorPaginatedQuery';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {BulkActionStatus, RunStatus} from '../types/globalTypes';
import {Alert} from '../ui/Alert';
import {Box} from '../ui/Box';
import {ButtonWIP} from '../ui/Button';
import {ButtonLink} from '../ui/ButtonLink';
import {ColorsWIP} from '../ui/Colors';
import {CursorPaginationControls} from '../ui/CursorControls';
import {Group} from '../ui/Group';
import {IconWIP} from '../ui/Icon';
import {Loading} from '../ui/Loading';
import {MenuItemWIP, MenuWIP} from '../ui/Menu';
import {NonIdealState} from '../ui/NonIdealState';
import {PageHeader} from '../ui/PageHeader';
import {Popover} from '../ui/Popover';
import {Table} from '../ui/Table';
import {TagWIP} from '../ui/TagWIP';
import {Heading, Mono} from '../ui/Text';
import {stringFromValue} from '../ui/TokenizingField';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {workspacePathFromAddress, workspacePipelinePath} from '../workspace/workspacePath';

import {BackfillTerminationDialog} from './BackfillTerminationDialog';
import {INSTANCE_HEALTH_FRAGMENT} from './InstanceHealthFragment';
import {InstanceTabs} from './InstanceTabs';
import {
  InstanceBackfillsQuery,
  InstanceBackfillsQueryVariables,
  InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results,
  InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet,
  InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_runs,
} from './types/InstanceBackfillsQuery';
import {InstanceHealthForBackfillsQuery} from './types/InstanceHealthForBackfillsQuery';

type Backfill = InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results;
type BackfillRun = InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_runs;

const PAGE_SIZE = 25;

export const InstanceBackfills = () => {
  const queryData = useQuery<InstanceHealthForBackfillsQuery>(INSTANCE_HEALTH_FOR_BACKFILLS_QUERY);

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
  useDocumentTitle('Backfills');

  return (
    <>
      <PageHeader
        title={<Heading>Instance status</Heading>}
        tabs={<InstanceTabs tab="backfills" queryData={queryData} />}
      />
      <Loading queryResult={queryResult} allowStaleData={true}>
        {({partitionBackfillsOrError}) => {
          if (partitionBackfillsOrError.__typename === 'PythonError') {
            return <PythonErrorInfo error={partitionBackfillsOrError} />;
          }

          if (!partitionBackfillsOrError.results.length) {
            return (
              <Box padding={{vertical: 64}}>
                <NonIdealState
                  icon="no-results"
                  title="No backfills found"
                  description={<p>This instance does not have any backfill jobs.</p>}
                />
              </Box>
            );
          }

          const daemonHealths = queryData.data?.instance.daemonHealth.allDaemonStatuses || [];
          const backfillHealths = daemonHealths
            .filter((daemon) => daemon.daemonType === 'BACKFILL')
            .map((daemon) => daemon.required && daemon.healthy);
          const isBackfillHealthy = backfillHealths.length && backfillHealths.every((x) => x);

          return (
            <div>
              {isBackfillHealthy ? null : (
                <Box padding={{horizontal: 24, vertical: 16}}>
                  <Alert
                    intent="warning"
                    title="The backfill daemon is not running."
                    description={
                      <div>
                        See the{' '}
                        <a
                          href="https://docs.dagster.io/deployment/dagster-daemon"
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
            </div>
          );
        }}
      </Loading>
    </>
  );
};

const INSTANCE_HEALTH_FOR_BACKFILLS_QUERY = gql`
  query InstanceHealthForBackfillsQuery {
    instance {
      ...InstanceHealthFragment
    }
  }

  ${INSTANCE_HEALTH_FRAGMENT}
`;

const BackfillTable = ({backfills, refetch}: {backfills: Backfill[]; refetch: () => void}) => {
  const [terminationBackfill, setTerminationBackfill] = React.useState<Backfill>();
  const [resumeBackfill] = useMutation(RESUME_BACKFILL_MUTATION);
  const [cancelRunBackfill, setCancelRunBackfill] = React.useState<Backfill>();
  const {canCancelPartitionBackfill} = usePermissions();

  const candidateId = terminationBackfill?.backfillId;

  React.useEffect(() => {
    if (canCancelPartitionBackfill && candidateId) {
      const [backfill] = backfills.filter((backfill) => backfill.backfillId === candidateId);
      setTerminationBackfill(backfill);
    }
  }, [backfills, candidateId, canCancelPartitionBackfill]);

  const resume = async (backfill: Backfill) => {
    const {data} = await resumeBackfill({variables: {backfillId: backfill.backfillId}});
    if (data && data.resumePartitionBackfill.__typename === 'ResumeBackfillSuccess') {
      refetch();
    } else if (data && data.resumePartitionBackfill.__typename === 'UnauthorizedError') {
      SharedToaster.show({
        message: (
          <Group direction="column" spacing={4}>
            <div>
              Attempted to retry the backfill in read-only mode. This backfill was not retried.
            </div>
          </Group>
        ),
        icon: 'error',
        intent: 'danger',
      });
    } else {
      const error = data.resumePartitionBackfill;
      SharedToaster.show({
        message: (
          <Group direction="column" spacing={4}>
            <div>An unexpected error occurred. This backfill was not retried.</div>
            <ButtonLink
              color={ColorsWIP.White}
              underline="always"
              onClick={() => {
                showCustomAlert({
                  body: <PythonErrorInfo error={error} />,
                });
              }}
            >
              View error
            </ButtonLink>
          </Group>
        ),
        icon: 'error',
        intent: 'danger',
      });
    }
  };

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
              onResumeBackfill={resume}
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
  onResumeBackfill,
}: {
  backfill: Backfill;
  onTerminateBackfill: (backfill: Backfill) => void;
  onResumeBackfill: (backfill: Backfill) => void;
}) => {
  const history = useHistory();
  const {canCancelPartitionBackfill, canLaunchPartitionBackfill} = usePermissions();
  const counts = React.useMemo(() => getProgressCounts(backfill), [backfill]);
  const runsUrl = `/instance/runs?${qs.stringify({
    q: stringFromValue([{token: 'tag', value: `dagster/backfill=${backfill.backfillId}`}]),
  })}`;

  const repoAddress = backfill.partitionSet
    ? buildRepoAddress(
        backfill.partitionSet.repositoryOrigin.repositoryName,
        backfill.partitionSet.repositoryOrigin.repositoryLocationName,
      )
    : null;
  const repo = useRepository(repoAddress);
  const isJob = !!(
    repo &&
    backfill.partitionSet &&
    isThisThingAJob(repo, backfill.partitionSet.pipelineName)
  );

  const partitionSetBackfillUrl = backfill.partitionSet
    ? workspacePipelinePath({
        repoName: backfill.partitionSet.repositoryOrigin.repositoryName,
        repoLocation: backfill.partitionSet.repositoryOrigin.repositoryLocationName,
        pipelineName: backfill.partitionSet.pipelineName,
        path: `/partitions?${qs.stringify({
          partitionSet: backfill.partitionSet.name,
          q: stringFromValue([{token: 'tag', value: `dagster/backfill=${backfill.backfillId}`}]),
        })}`,
        isJob,
      })
    : null;

  const canCancel = backfill.runs.some((run) => run.canTerminate);

  return (
    <tr>
      <td style={{width: '120px'}}>
        <Mono>
          {partitionSetBackfillUrl ? (
            <Link to={partitionSetBackfillUrl}>{backfill.backfillId}</Link>
          ) : (
            backfill.backfillId
          )}
        </Mono>
      </td>
      <td>
        {backfill.partitionSet ? (
          <PartitionSetReference partitionSet={backfill.partitionSet} />
        ) : (
          backfill.partitionSetName
        )}
      </td>
      <td style={{textAlign: 'right'}}>
        <BackfillProgress backfill={backfill} />
      </td>
      <td>
        {[BulkActionStatus.CANCELED, BulkActionStatus.FAILED].includes(backfill.status) ? (
          <Box margin={{bottom: 12}}>
            <TagButton
              onClick={() =>
                backfill.error &&
                showCustomAlert({title: 'Error', body: <PythonErrorInfo error={backfill.error} />})
              }
            >
              <TagWIP intent="danger" interactive>
                {backfill.status}
              </TagWIP>
            </TagButton>
          </Box>
        ) : null}
        <BackfillStatusTable backfill={backfill} />
      </td>
      <td>{backfill.timestamp ? <TimestampDisplay timestamp={backfill.timestamp} /> : '-'}</td>
      <td style={{width: '100px'}}>
        <Popover
          content={
            <MenuWIP>
              {canCancelPartitionBackfill ? (
                <>
                  {counts.numUnscheduled && backfill.status === BulkActionStatus.REQUESTED ? (
                    <MenuItemWIP
                      text="Cancel backfill submission"
                      icon="cancel"
                      intent="danger"
                      onClick={() => onTerminateBackfill(backfill)}
                    />
                  ) : null}
                  {canCancel ? (
                    <MenuItemWIP
                      text="Terminate unfinished runs"
                      icon="cancel"
                      intent="danger"
                      onClick={() => onTerminateBackfill(backfill)}
                    />
                  ) : null}
                </>
              ) : null}
              {canLaunchPartitionBackfill &&
              backfill.status === BulkActionStatus.FAILED &&
              backfill.partitionSet ? (
                <MenuItemWIP
                  text="Resume failed backfill"
                  title="Submits runs for all partitions in the backfill that do not have a corresponding run. Does not retry failed runs."
                  icon="refresh"
                  onClick={() => onResumeBackfill(backfill)}
                />
              ) : null}
              {partitionSetBackfillUrl ? (
                <MenuItemWIP
                  text="View Partition Matrix"
                  icon="view_list"
                  onClick={() => history.push(partitionSetBackfillUrl)}
                />
              ) : null}
              <MenuItemWIP
                text="View Backfill Runs"
                icon="settings_backup_restore"
                onClick={() => history.push(runsUrl)}
              />
            </MenuWIP>
          }
          position="bottom-right"
        >
          <ButtonWIP icon={<IconWIP name="expand_more" />} />
        </Popover>
      </td>
    </tr>
  );
};

const TagButton = styled.button`
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
  margin: 0;

  :focus {
    outline: none;
  }
`;

const getProgressCounts = (backfill: Backfill) => {
  const byPartitionRuns: {[key: string]: BackfillRun} = {};
  backfill.runs.forEach((run) => {
    const [runPartitionName] = run.tags
      .filter((tag) => tag.key === DagsterTag.Partition)
      .map((tag) => tag.value);

    if (runPartitionName && !byPartitionRuns[runPartitionName]) {
      byPartitionRuns[runPartitionName] = run;
    }
  });

  const latestPartitionRuns = Object.values(byPartitionRuns);
  const {numQueued, numInProgress, numSucceeded, numFailed} = latestPartitionRuns.reduce(
    (accum: any, {status}: {status: RunStatus}) => {
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
    numUnscheduled: backfill.numTotal - backfill.numRequested,
    numSkipped: backfill.numRequested - latestPartitionRuns.length,
    numTotal: backfill.numTotal,
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
        lineHeight: '32px',
        fontSize: '36px',
        fontWeight: 600,
        color: ColorsWIP.Gray600,
      }}
    >
      {numTotal ? Math.floor((100 * numCompleted) / numTotal) : '-'}%
    </span>
  );
};

const PartitionSetReference: React.FunctionComponent<{
  partitionSet: InstanceBackfillsQuery_partitionBackfillsOrError_PartitionBackfills_results_partitionSet;
}> = ({partitionSet}) => {
  const repoAddress = buildRepoAddress(
    partitionSet.repositoryOrigin.repositoryName,
    partitionSet.repositoryOrigin.repositoryLocationName,
  );
  const repo = useRepository(repoAddress);
  const isJob = !!(repo && isThisThingAJob(repo, partitionSet.pipelineName));

  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <Link
        to={workspacePipelinePath({
          repoName: partitionSet.repositoryOrigin.repositoryName,
          repoLocation: partitionSet.repositoryOrigin.repositoryLocationName,
          pipelineName: partitionSet.pipelineName,
          isJob,
          path: `/partitions?partitionSet=${encodeURIComponent(partitionSet.name)}`,
        })}
      >
        {partitionSet.name}
      </Link>
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
        <IconWIP name="repo" color={ColorsWIP.Gray400} />
        <Link to={workspacePathFromAddress(repoAddress)}>{repoAddressAsString(repoAddress)}</Link>
      </Box>
      <PipelineReference
        showIcon
        size="small"
        pipelineName={partitionSet.pipelineName}
        pipelineHrefContext={{
          name: partitionSet.repositoryOrigin.repositoryName,
          location: partitionSet.repositoryOrigin.repositoryLocationName,
        }}
        isJob={isJob}
      />
    </Box>
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
    <StyledTable>
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
    </StyledTable>
  );
};

const StyledTable = styled.table`
  max-width: 250px;
  border-collapse: collapse;

  &&& tr td {
    box-shadow: none !important;
    padding: 0 24px 4px 0;
    margin: 0;
  }

  &&& tr td:last-child {
    padding-right: 0;
    text-align: right;
  }

  &&& tr.total td {
    font-weight: 600;
  }
`;

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
    <tr className={isTotal ? 'total' : undefined}>
      <td>{label}</td>
      <td>{count}</td>
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
          runs {
            id
            canTerminate
            status
            tags {
              key
              value
            }
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
          error {
            ...PythonErrorFragment
          }
        }
      }
      ...PythonErrorFragment
    }
  }

  ${PYTHON_ERROR_FRAGMENT}
`;

const RESUME_BACKFILL_MUTATION = gql`
  mutation resumeBackfill($backfillId: String!) {
    resumePartitionBackfill(backfillId: $backfillId) {
      __typename
      ... on ResumeBackfillSuccess {
        backfillId
      }
      ... on UnauthorizedError {
        message
      }
      ... on PythonError {
        message
      }
    }
  }
`;
