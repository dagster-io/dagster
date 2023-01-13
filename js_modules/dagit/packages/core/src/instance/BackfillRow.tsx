import {gql, useLazyQuery} from '@apollo/client';
import {Box, Button, Colors, Icon, MenuItem, Menu, Popover, Tag, Mono} from '@dagster-io/ui';
import * as React from 'react';
import {useHistory, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {usePermissionsDEPRECATED} from '../app/Permissions';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RunStatus, BulkActionStatus} from '../graphql/types';
import {
  PartitionState,
  PartitionStatus,
  PartitionStatusCountsOnly,
  runStatusToPartitionState,
} from '../partitions/PartitionStatus';
import {PipelineReference} from '../pipelines/PipelineReference';
import {AssetKeyTagCollection} from '../runs/AssetKeyTagCollection';
import {inProgressStatuses} from '../runs/RunStatuses';
import {runsPathWithFilters} from '../runs/RunsFilterInput';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {LoadingOrNone, useDelayedRowQuery} from '../workspace/VirtualizedWorkspaceTable';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {workspacePathFromAddress, workspacePipelinePath} from '../workspace/workspacePath';

import {
  PartitionStatusesForBackfillFragment,
  SingleBackfillQuery,
  SingleBackfillQueryVariables,
} from './types/BackfillRow.types';
import {BackfillTableFragment} from './types/BackfillTable.types';

type BackfillPartitionStatusData = PartitionStatusesForBackfillFragment;

export const BackfillRow = ({
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
  const [queryBackfill, queryResult] = useLazyQuery<
    SingleBackfillQuery,
    SingleBackfillQueryVariables
  >(SINGLE_BACKFILL_QUERY, {
    variables: {
      backfillId: backfill.backfillId,
    },
    notifyOnNetworkStatusChange: true,
  });

  useDelayedRowQuery(queryBackfill);
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {data} = queryResult;
  const backfillStatusData = React.useMemo(() => {
    if (data?.partitionBackfillOrError.__typename !== 'PartitionBackfill') {
      return null;
    }

    return data.partitionBackfillOrError.partitionStatuses;
  }, [data]);

  const runsUrl = runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${backfill.backfillId}`,
    },
  ]);

  return (
    <tr>
      <td style={{width: 120}}>
        <Mono style={{fontSize: '16px', lineHeight: '18px'}}>
          <Link to={runsUrl}>{backfill.backfillId}</Link>
        </Mono>
      </td>
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
        {backfillStatusData ? (
          <BackfillStatus backfill={backfill} statusData={backfillStatusData} />
        ) : (
          <LoadingOrNone queryResult={queryResult} />
        )}
      </td>
      <td>
        {backfillStatusData ? (
          <BackfillRunStatus
            backfill={backfill}
            statusData={backfillStatusData}
            history={history}
          />
        ) : (
          <LoadingOrNone queryResult={queryResult} />
        )}
      </td>
      <td>
        {backfillStatusData ? (
          <BackfillMenu
            backfill={backfill}
            statusData={backfillStatusData}
            history={history}
            onResumeBackfill={onResumeBackfill}
            onTerminateBackfill={onTerminateBackfill}
            onShowStepStatus={onShowStepStatus}
          />
        ) : (
          <LoadingOrNone queryResult={queryResult} />
        )}
      </td>
    </tr>
  );
};
const BackfillMenu = ({
  backfill,
  statusData,
  history,
  onTerminateBackfill,
  onResumeBackfill,
  onShowStepStatus,
}: {
  backfill: BackfillTableFragment;
  statusData: BackfillPartitionStatusData;
  history: any;
  onTerminateBackfill: (backfill: BackfillTableFragment) => void;
  onResumeBackfill: (backfill: BackfillTableFragment) => void;
  onShowStepStatus: (backfill: BackfillTableFragment) => void;
}) => {
  const {canCancelPartitionBackfill, canLaunchPartitionBackfill} = usePermissionsDEPRECATED();
  const runsUrl = runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${backfill.backfillId}`,
    },
  ]);

  const canCancelRuns = statusData.results.some(
    (r) => r.runStatus === RunStatus.QUEUED || r.runStatus === RunStatus.STARTED,
  );

  return (
    <Popover
      content={
        <Menu>
          {canCancelPartitionBackfill.enabled ? (
            <>
              {backfill.numCancelable > 0 ? (
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
  );
};
const BACKFILL_PARTITIONS_COUNTS_THRESHOLD = 1000;

const BackfillRunStatus = ({
  backfill,
  statusData,
  history,
}: {
  backfill: BackfillTableFragment;
  history: any;
  statusData: BackfillPartitionStatusData;
}) => {
  const states = React.useMemo(
    () =>
      Object.fromEntries(
        statusData.results.map((s) => [s.partitionName, runStatusToPartitionState(s.runStatus)]),
      ),
    [statusData],
  );

  return statusData.results.length > BACKFILL_PARTITIONS_COUNTS_THRESHOLD ? (
    <PartitionStatusCountsOnly
      partitionNames={backfill.partitionNames}
      partitionStateForKey={(key) => states[key]}
    />
  ) : (
    <PartitionStatus
      partitionNames={backfill.partitionNames}
      partitionStateForKey={(key) => states[key]}
      splitPartitions={true}
      onClick={(partitionName) => {
        const entry = statusData.results.find((r) => r.partitionName === partitionName);
        if (entry) {
          history.push(`/runs/${entry.runId}`);
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
  const isHiddenAssetPartitionSet = isHiddenAssetGroupJob(partitionSetName || '');

  const buildHeader = () => {
    if (isHiddenAssetPartitionSet) {
      return null;
    }
    if (partitionSet && repo) {
      return (
        <Link
          style={{fontWeight: 500}}
          to={workspacePipelinePath({
            repoName: partitionSet.repositoryOrigin.repositoryName,
            repoLocation: partitionSet.repositoryOrigin.repositoryLocationName,
            pipelineName: partitionSet.pipelineName,
            isJob: isThisThingAJob(repo, partitionSet.pipelineName),
            path: `/partitions?partitionSet=${encodeURIComponent(partitionSet.name)}`,
          })}
        >
          {partitionSet.name}
        </Link>
      );
    }
    return <span style={{fontWeight: 500}}>{partitionSetName}</span>;
  };

  const buildRepoLink = () =>
    repoAddress ? (
      <Box flex={{direction: 'row', gap: 8, alignItems: 'center'}} style={{fontSize: '12px'}}>
        <Icon name="repo" color={Colors.Gray400} />
        <Link to={workspacePathFromAddress(repoAddress)}>
          {repoAddressAsHumanString(repoAddress)}
        </Link>
      </Box>
    ) : undefined;

  const buildPipelineOrAssets = () => {
    if (isHiddenAssetPartitionSet) {
      return <AssetKeyTagCollection assetKeys={assetSelection} modalTitle="Assets in backfill" />;
    }
    if (partitionSet && repo) {
      return (
        <PipelineReference
          showIcon
          size="small"
          pipelineName={partitionSet.pipelineName}
          pipelineHrefContext={{
            name: partitionSet.repositoryOrigin.repositoryName,
            location: partitionSet.repositoryOrigin.repositoryLocationName,
          }}
          isJob={isThisThingAJob(repo, partitionSet.pipelineName)}
        />
      );
    }
    return null;
  };

  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {buildHeader()}
      <Box flex={{direction: 'column', gap: 4}} style={{fontSize: '12px'}}>
        {buildRepoLink()}
        {buildPipelineOrAssets()}
      </Box>
    </Box>
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
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <div>
        <TagButton onClick={onExpand}>
          <Tag intent="primary" interactive>
            {backfill.partitionNames.length} partitions
          </Tag>
        </TagButton>
      </div>
      {allPartitions.length > BACKFILL_PARTITIONS_COUNTS_THRESHOLD ? (
        <PartitionStatusCountsOnly
          partitionNames={allPartitions}
          partitionStateForKey={() => PartitionState.QUEUED}
          small
        />
      ) : (
        <PartitionStatus
          partitionNames={allPartitions}
          partitionStateForKey={() => PartitionState.QUEUED}
          hideStatusTooltip
          small
        />
      )}
    </Box>
  );
};

const BackfillStatus = ({
  backfill,
  statusData,
}: {
  backfill: BackfillTableFragment;
  statusData: BackfillPartitionStatusData;
}) => {
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
      const statuses = statusData.results.map((r) => r.runStatus);
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

export const SINGLE_BACKFILL_QUERY = gql`
  query SingleBackfillQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        backfillId
        partitionStatuses {
          ...PartitionStatusesForBackfill
        }
      }
    }
  }

  fragment PartitionStatusesForBackfill on PartitionStatuses {
    results {
      id
      partitionName
      runId
      runStatus
    }
  }
`;
