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
} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {SharedToaster} from '../app/DomUtils';
import {usePermissions} from '../app/Permissions';
import {PYTHON_ERROR_FRAGMENT} from '../app/PythonErrorFragment';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PartitionStatus} from '../partitions/PartitionStatus';
import {PipelineReference} from '../pipelines/PipelineReference';
import {AssetKeyTagCollection} from '../runs/AssetKeyTagCollection';
import {inProgressStatuses} from '../runs/RunStatuses';
import {runsPathWithFilters} from '../runs/RunsFilterInput';
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
import {BackfillTableFragment} from './types/BackfillTableFragment';
import {resumeBackfill, resumeBackfillVariables} from './types/resumeBackfill';

export const BackfillTable = ({
  showBackfillTarget = true,
  allPartitions,
  backfills,
  refetch,
}: {
  allPartitions?: string[];
  backfills: BackfillTableFragment[];
  refetch: () => void;
  showBackfillTarget?: boolean;
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
  const {canCancelPartitionBackfill} = usePermissions();

  const candidateId = terminationBackfill?.backfillId;

  React.useEffect(() => {
    if (canCancelPartitionBackfill.enabled && candidateId) {
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

  return (
    <>
      <Table>
        <thead>
          <tr>
            <th style={{width: 120}}>Backfill ID</th>
            <th style={{width: 200}}>Created</th>
            {showBackfillTarget ? <th>Backfill target</th> : null}
            {allPartitions ? <th>Requested</th> : null}
            <th style={{width: 140}}>Backfill status</th>
            <th>Run status</th>
            <th style={{width: 80}} />
          </tr>
        </thead>
        <tbody>
          {backfills.map((backfill: BackfillTableFragment) => (
            <BackfillRow
              key={backfill.backfillId}
              showBackfillTarget={showBackfillTarget}
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
    </>
  );
};

const BackfillRow = ({
  backfill,
  allPartitions,
  showBackfillTarget,
  onTerminateBackfill,
  onResumeBackfill,
  onShowStepStatus,
  onShowPartitionsRequested,
}: {
  backfill: BackfillTableFragment;
  allPartitions?: string[];
  onTerminateBackfill: (backfill: BackfillTableFragment) => void;
  onResumeBackfill: (backfill: BackfillTableFragment) => void;
  showBackfillTarget: boolean;
  onShowStepStatus: (backfill: BackfillTableFragment) => void;
  onShowPartitionsRequested: (backfill: BackfillTableFragment) => void;
}) => {
  const history = useHistory();
  const {canCancelPartitionBackfill, canLaunchPartitionBackfill} = usePermissions();
  const runsUrl = runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${backfill.backfillId}`,
    },
  ]);

  const canCancelRuns = backfill.partitionStatuses.results.some(
    (r) => r.runStatus === RunStatus.QUEUED || r.runStatus === RunStatus.STARTED,
  );

  return (
    <tr>
      <td style={{width: 120}}>{backfill.backfillId}</td>
      <td style={{width: 240}}>
        {backfill.timestamp ? <TimestampDisplay timestamp={backfill.timestamp} /> : '-'}
      </td>
      {showBackfillTarget ? (
        <td>
          <BackfillTarget backfill={backfill} />
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
      <td style={{width: 140}}>
        <BackfillStatus backfill={backfill} />
      </td>
      <td>
        <BackfillRunStatus backfill={backfill} history={history} />
      </td>
      <td>
        <Popover
          content={
            <Menu>
              {canCancelPartitionBackfill.enabled ? (
                <>
                  {backfill.numRequested < backfill.partitionStatuses.results.length &&
                  backfill.status === BulkActionStatus.REQUESTED ? (
                    <MenuItem
                      text="Cancel backfill submission"
                      icon="cancel"
                      intent="danger"
                      onClick={() => onTerminateBackfill(backfill)}
                    />
                  ) : null}
                  {canCancelRuns ? (
                    <MenuItem
                      text="Terminate unfinished runs"
                      icon="cancel"
                      intent="danger"
                      onClick={() => onTerminateBackfill(backfill)}
                    />
                  ) : null}
                </>
              ) : null}
              {canLaunchPartitionBackfill.enabled &&
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
                text="View backfill runs"
                icon="settings_backup_restore"
                onClick={() => history.push(runsUrl)}
              />
              <MenuItem
                text="View step status"
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
      const statuses = backfill.partitionStatuses.results.map((r) => r.runStatus);
      if (
        statuses.filter((runStatus) => runStatus === RunStatus.SUCCESS).length ===
        backfill.partitionNames.length
      ) {
        return <Tag intent="success">Completed</Tag>;
      }
      if (statuses.filter((runStatus) => runStatus && runStatus in inProgressStatuses).length) {
        return <Tag intent="primary">In progress</Tag>;
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
  backfill.partitionStatuses.results.forEach((s) => {
    partitionData[s.partitionName] = s.runStatus;
    partitionRun[s.partitionName] = s.runId;
  });

  return (
    <PartitionStatus
      partitionNames={backfill.partitionNames}
      partitionData={partitionData}
      splitPartitions={true}
      onClick={(partitionName) => {
        if (partitionRun[partitionName]) {
          history.push(`/instance/runs/${partitionRun[partitionName]}`);
        }
      }}
    />
  );
};

const BackfillTarget: React.FC<{
  backfill: BackfillTableFragment;
}> = ({backfill}) => {
  const {assetSelection, partitionSet, partitionSetName} = backfill;

  const repoAddress = partitionSet
    ? buildRepoAddress(
        partitionSet.repositoryOrigin.repositoryName,
        partitionSet.repositoryOrigin.repositoryLocationName,
      )
    : null;

  const repo = useRepository(repoAddress);

  if (!partitionSet || !repoAddress) {
    return <span>{partitionSetName}</span>;
  }

  const isJob = !!(repo && isThisThingAJob(repo, partitionSet.pipelineName));
  const isHiddenAssetJob = isHiddenAssetGroupJob(partitionSet.pipelineName);

  const repoLink = (
    <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}}>
      <Icon name="repo" color={Colors.Gray400} />
      <Link to={workspacePathFromAddress(repoAddress)}>{repoAddressAsString(repoAddress)}</Link>
    </Box>
  );

  if (isHiddenAssetJob) {
    return (
      <Box flex={{direction: 'column', gap: 8}}>
        {repoLink}
        <AssetKeyTagCollection assetKeys={assetSelection} modalTitle="Assets in Backfill" />
      </Box>
    );
  }

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
      {repoLink}
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
    numRequested
    partitionNames
    numPartitions
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
    partitionStatuses {
      results {
        id
        partitionName
        runId
        runStatus
      }
    }
    assetSelection {
      path
    }
    error {
      ...PythonErrorFragment
    }
  }
  ${PYTHON_ERROR_FRAGMENT}
`;
