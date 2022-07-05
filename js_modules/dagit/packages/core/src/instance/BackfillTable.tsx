import {gql, useMutation} from '@apollo/client';
import {
  Box,
  Button,
  Colors,
  Group,
  Icon,
  MenuItem,
  Menu,
  Popover,
  Table,
  Tag,
  Mono,
  stringFromValue,
} from '@dagster-io/ui';
import qs from 'qs';
import * as React from 'react';
import {useHistory, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {usePermissions} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {PartitionStatus} from '../partitions/PartitionStatus';
import {PipelineReference} from '../pipelines/PipelineReference';
import {
  doneStatuses,
  failedStatuses,
  inProgressStatuses,
  queuedStatuses,
  successStatuses,
} from '../runs/RunStatuses';
import {DagsterTag} from '../runs/RunTag';
import {runsPathWithFilters} from '../runs/RunsFilterInput';
import {TerminationDialog} from '../runs/TerminationDialog';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {BulkActionStatus, RunStatus} from '../types/globalTypes';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsString} from '../workspace/repoAddressAsString';
import {workspacePathFromAddress, workspacePipelinePath} from '../workspace/workspacePath';

import {BackfillPartitionsRequestedDialog} from './BackfillPartitionsRequestedDialog';
import {BackfillStepStatusDialog} from './BackfillStepStatusDialog';
import {BackfillTerminationDialog} from './BackfillTerminationDialog';
import {RESUME_BACKFILL_MUTATION} from './BackfillUtils';
import {
  BackfillTableFragment,
  BackfillTableFragment_runs,
  BackfillTableFragment_partitionSet,
} from './types/BackfillTableFragment';
import {resumeBackfill, resumeBackfillVariables} from './types/resumeBackfill';

type BackfillRun = BackfillTableFragment_runs;

export const BackfillTable = ({
  showPartitionSet = true,
  allPartitions,
  backfills,
  refetch,
}: {
  allPartitions?: string[];
  backfills: BackfillTableFragment[];
  refetch: () => void;
  showPartitionSet?: boolean;
}) => {
  const [terminationBackfill, setTerminationBackfill] = React.useState<BackfillTableFragment>();
  const [stepStatusBackfill, setStepStatusBackfill] = React.useState<BackfillTableFragment>();
  const [
    partitionsRequestedBackfill,
    setPartitionsRequestedBackfill,
  ] = React.useState<BackfillTableFragment>();
  const [resumeBackfill] = useMutation<resumeBackfill, resumeBackfillVariables>(
    RESUME_BACKFILL_MUTATION,
  );
  const [cancelRunBackfill, setCancelRunBackfill] = React.useState<BackfillTableFragment>();
  const {canCancelPartitionBackfill} = usePermissions();

  const candidateId = terminationBackfill?.backfillId;

  React.useEffect(() => {
    if (canCancelPartitionBackfill && candidateId) {
      const [backfill] = backfills.filter((backfill) => backfill.backfillId === candidateId);
      setTerminationBackfill(backfill);
    }
  }, [backfills, candidateId, canCancelPartitionBackfill]);

  const resume = async (backfill: BackfillTableFragment) => {
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
    } else if (data && data.resumePartitionBackfill.__typename === 'PythonError') {
      const error = data.resumePartitionBackfill;
      SharedToaster.show({
        message: <div>An unexpected error occurred. This backfill was not retried.</div>,
        icon: 'error',
        intent: 'danger',
        action: {
          text: 'View error',
          onClick: () =>
            showCustomAlert({
              body: <PythonErrorInfo error={error} />,
            }),
        },
      });
    }
  };

  const unfinishedRuns = cancelRunBackfill?.unfinishedRuns;
  const unfinishedMap =
    unfinishedRuns?.reduce((accum, run) => ({...accum, [run.id]: run.canTerminate}), {}) || {};

  return (
    <>
      <Table>
        <thead>
          <tr>
            <th style={{width: 120}}>Backfill Id</th>
            <th style={{width: 200}}>Created</th>
            {showPartitionSet ? <th>Partition Set</th> : null}
            {allPartitions ? <th>Requested</th> : null}
            <th style={{textAlign: 'right', width: 200}}>Backfill Status</th>
            <th>Run Status</th>
            <th style={{width: 80}} />
          </tr>
        </thead>
        <tbody>
          {backfills.map((backfill: BackfillTableFragment) => (
            <BackfillRow
              key={backfill.backfillId}
              showPartitionSet={showPartitionSet}
              backfill={backfill}
              allPartitions={allPartitions}
              onTerminateBackfill={setTerminationBackfill}
              onResumeBackfill={resume}
              onShowStepStatus={setStepStatusBackfill}
              onShowPartitionsRequested={setPartitionsRequestedBackfill}
            />
          ))}
        </tbody>
      </Table>
      <BackfillStepStatusDialog
        backfill={stepStatusBackfill}
        onClose={() => setStepStatusBackfill(undefined)}
      />
      <BackfillPartitionsRequestedDialog
        backfill={partitionsRequestedBackfill}
        onClose={() => setPartitionsRequestedBackfill(undefined)}
      />
      <BackfillTerminationDialog
        backfill={terminationBackfill}
        onClose={() => setTerminationBackfill(undefined)}
        onComplete={() => refetch()}
      />
      <TerminationDialog
        isOpen={!!unfinishedRuns?.length}
        onClose={() => setCancelRunBackfill(undefined)}
        onComplete={() => refetch()}
        selectedRuns={unfinishedMap}
      />
    </>
  );
};

const BackfillRow = ({
  backfill,
  allPartitions,
  showPartitionSet,
  onTerminateBackfill,
  onResumeBackfill,
  onShowStepStatus,
  onShowPartitionsRequested,
}: {
  backfill: BackfillTableFragment;
  allPartitions?: string[];
  onTerminateBackfill: (backfill: BackfillTableFragment) => void;
  onResumeBackfill: (backfill: BackfillTableFragment) => void;
  showPartitionSet: boolean;
  onShowStepStatus: (backfill: BackfillTableFragment) => void;
  onShowPartitionsRequested: (backfill: BackfillTableFragment) => void;
}) => {
  const history = useHistory();
  const {canCancelPartitionBackfill, canLaunchPartitionBackfill} = usePermissions();
  const counts = React.useMemo(() => getProgressCounts(backfill), [backfill]);
  const runsUrl = runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${backfill.backfillId}`,
    },
  ]);

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
          q: [stringFromValue([{token: 'tag', value: `dagster/backfill=${backfill.backfillId}`}])],
        })}`,
        isJob,
      })
    : null;

  const canCancel = backfill.runs.some((run) => run.canTerminate);

  return (
    <tr>
      <td style={{width: 120}}>
        <Mono>
          {partitionSetBackfillUrl ? (
            <Link to={partitionSetBackfillUrl}>{backfill.backfillId}</Link>
          ) : (
            backfill.backfillId
          )}
        </Mono>
      </td>
      <td style={{width: 240}}>
        {backfill.timestamp ? <TimestampDisplay timestamp={backfill.timestamp} /> : '-'}
      </td>
      {showPartitionSet ? (
        <td>
          {backfill.partitionSet ? (
            <PartitionSetReference partitionSet={backfill.partitionSet} />
          ) : (
            backfill.partitionSetName
          )}
        </td>
      ) : null}
      {allPartitions ? (
        <td style={{width: 300}}>
          <BackfillRequested
            allPartitions={allPartitions}
            backfill={backfill}
            onExpand={() => onShowPartitionsRequested(backfill)}
          />
        </td>
      ) : null}
      <td style={{textAlign: 'right', width: 200}}>
        <BackfillStatus backfill={backfill} />
      </td>
      <td>
        <BackfillRunStatus backfill={backfill} history={history} />
      </td>
      <td>
        <Popover
          content={
            <Menu>
              {canCancelPartitionBackfill ? (
                <>
                  {counts.numUnscheduled && backfill.status === BulkActionStatus.REQUESTED ? (
                    <MenuItem
                      text="Cancel backfill submission"
                      icon="cancel"
                      intent="danger"
                      onClick={() => onTerminateBackfill(backfill)}
                    />
                  ) : null}
                  {canCancel ? (
                    <MenuItem
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
                <MenuItem
                  text="Resume failed backfill"
                  title="Submits runs for all partitions in the backfill that do not have a corresponding run. Does not retry failed runs."
                  icon="refresh"
                  onClick={() => onResumeBackfill(backfill)}
                />
              ) : null}
              <MenuItem
                text="View Backfill Runs"
                icon="settings_backup_restore"
                onClick={() => history.push(runsUrl)}
              />
              <MenuItem
                text="View Step Status"
                icon="view_list"
                onClick={() => {
                  onShowStepStatus(backfill);
                }}
              />
            </Menu>
          }
          position="bottom-right"
        >
          <Button icon={<Icon name="expand_more" />} />
        </Popover>
      </td>
    </tr>
  );
};

const BackfillRequested = ({
  allPartitions,
  backfill,
  onExpand,
}: {
  allPartitions: string[];
  backfill: BackfillTableFragment;
  onExpand: () => void;
}) => {
  const partitionData = {};
  backfill.partitionNames.forEach((partitionName) => {
    // kind of a hack, but set status here to get the coloring we want
    partitionData[partitionName] = RunStatus.QUEUED;
  });
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <div>
        <TagButton onClick={onExpand}>
          <Tag intent="primary" interactive>
            {backfill.partitionNames.length} partitions
          </Tag>
        </TagButton>
      </div>
      <PartitionStatus
        partitionNames={allPartitions}
        partitionData={partitionData}
        small
        hideStatusTooltip
      />
    </Box>
  );
};

const BackfillStatus = ({backfill}: {backfill: BackfillTableFragment}) => {
  switch (backfill.status) {
    case BulkActionStatus.REQUESTED:
      return <Tag>Requested</Tag>;
    case BulkActionStatus.CANCELED:
    case BulkActionStatus.FAILED:
      return (
        <Box margin={{bottom: 12}}>
          <TagButton
            onClick={() =>
              backfill.error &&
              showCustomAlert({title: 'Error', body: <PythonErrorInfo error={backfill.error} />})
            }
          >
            <Tag intent="danger">{backfill.status === 'FAILED' ? 'Failed' : 'Canceled'}</Tag>
          </TagButton>
        </Box>
      );
    case BulkActionStatus.COMPLETED:
      const runStatuses = backfill.runs.map((run) => run.status);
      const isDone = runStatuses.every((status) => doneStatuses.has(status));
      if (!isDone) {
        return <Tag intent="primary">In progress</Tag>;
      }
      if (
        runStatuses.filter((status) => successStatuses.has(status)).length ===
        backfill.partitionNames.length
      ) {
        return <Tag intent="success">Completed</Tag>;
      }
      return <Tag intent="warning">Incomplete</Tag>;
  }
};

const BackfillRunStatus = ({
  backfill,
  history,
}: {
  backfill: BackfillTableFragment;
  history: any;
}) => {
  const partitionData = {};
  const partitionRun = {};
  backfill.runs.forEach((run) => {
    run.tags.forEach((tag) => {
      if (tag.key === DagsterTag.Partition) {
        partitionData[tag.value] = run.status;
        partitionRun[tag.value] = run;
      }
    });
  });

  return (
    <PartitionStatus
      partitionNames={backfill.partitionNames}
      partitionData={partitionData}
      splitPartitions={true}
      onClick={(partitionName) => {
        if (partitionRun[partitionName]) {
          history.push(`/instance/runs/${partitionRun[partitionName].id}`);
        }
      }}
    />
  );
};

const PartitionSetReference: React.FC<{
  partitionSet: BackfillTableFragment_partitionSet;
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
        <Icon name="repo" color={Colors.Gray400} />
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

const getProgressCounts = (backfill: BackfillTableFragment) => {
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

  const numTotal = backfill.partitionNames.length;

  return {
    numQueued,
    numInProgress,
    numSucceeded,
    numFailed,
    numUnscheduled: numTotal - backfill.numRequested,
    numSkipped: backfill.numRequested - latestPartitionRuns.length,
    numTotal,
  };
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

export const BACKFILL_TABLE_FRAGMENT = gql`
  fragment BackfillTableFragment on PartitionBackfill {
    backfillId
    status
    backfillStatus
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
    runs {
      id
      canTerminate
      status
      tags {
        key
        value
      }
    }
    unfinishedRuns {
      id
      canTerminate
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
  ${PYTHON_ERROR_FRAGMENT}
`;
