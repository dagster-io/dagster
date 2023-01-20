import {gql, useLazyQuery} from '@apollo/client';
import {Box, Button, Colors, Icon, MenuItem, Menu, Popover, Tag, Mono} from '@dagster-io/ui';
import countBy from 'lodash/countBy';
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
  runStatusToPartitionState,
} from '../partitions/PartitionStatus';
import {PipelineReference} from '../pipelines/PipelineReference';
import {AssetKeyTagCollection} from '../runs/AssetKeyTagCollection';
import {inProgressStatuses} from '../runs/RunStatuses';
import {RunStatusTagsWithCounts} from '../runs/RunTimeline';
import {runsPathWithFilters} from '../runs/RunsFilterInput';
import {TimestampDisplay} from '../schedules/TimestampDisplay';
import {LoadingOrNone, useDelayedRowQuery} from '../workspace/VirtualizedWorkspaceTable';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {workspacePathFromAddress, workspacePipelinePath} from '../workspace/workspacePath';

import {
  PartitionStatusesForBackfillFragment,
  SingleBackfillCountsQuery,
  SingleBackfillCountsQueryVariables,
  SingleBackfillQuery,
  SingleBackfillQueryVariables,
} from './types/BackfillRow.types';
import {BackfillTableFragment} from './types/BackfillTable.types';

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
  const statusDetails = useLazyQuery<SingleBackfillQuery, SingleBackfillQueryVariables>(
    SINGLE_BACKFILL_STATUS_DETAILS_QUERY,
    {
      variables: {backfillId: backfill.backfillId},
      notifyOnNetworkStatusChange: true,
    },
  );

  const statusCounts = useLazyQuery<SingleBackfillCountsQuery, SingleBackfillCountsQueryVariables>(
    SINGLE_BACKFILL_STATUS_COUNTS_QUERY,
    {
      variables: {backfillId: backfill.backfillId},
      notifyOnNetworkStatusChange: true,
    },
  );

  // Note: We switch queries based on how many partitions there are to display,
  // because the detail is nice for small backfills but breaks for 100k+ partitions
  const [queryStatus, queryResult] =
    backfill.numPartitions > BACKFILL_PARTITIONS_COUNTS_THRESHOLD ? statusCounts : statusDetails;

  useDelayedRowQuery(queryStatus);
  useQueryRefreshAtInterval(queryResult, FIFTEEN_SECONDS);

  const {data} = queryResult;
  const {counts, statuses} = React.useMemo(() => {
    if (data?.partitionBackfillOrError.__typename !== 'PartitionBackfill') {
      return {counts: null, statuses: null};
    }
    if ('partitionStatusCounts' in data.partitionBackfillOrError) {
      const counts = Object.fromEntries(
        data.partitionBackfillOrError.partitionStatusCounts.map((e) => [e.runStatus, e.count]),
      );
      return {counts, statuses: null};
    }
    const statuses = data.partitionBackfillOrError.partitionStatuses.results;
    const counts = countBy(statuses, (k) => k.runStatus);
    return {counts, statuses};
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
      <td style={{width: 220}}>
        {backfill.timestamp ? <TimestampDisplay timestamp={backfill.timestamp} /> : '-'}
      </td>
      {showBackfillTarget ? (
        <td style={{width: '20%'}}>
          <BackfillTarget backfill={backfill} />
        </td>
      ) : null}
      <td style={{width: allPartitions ? 300 : 140}}>
        <BackfillRequestedRange
          backfill={backfill}
          allPartitions={allPartitions}
          onExpand={() => onShowPartitionsRequested(backfill)}
        />
      </td>
      <td style={{width: 140}}>
        {counts ? (
          <BackfillStatusTag backfill={backfill} counts={counts} />
        ) : (
          <LoadingOrNone queryResult={queryResult} />
        )}
      </td>
      <td>
        {counts ? (
          <BackfillRunStatus backfill={backfill} counts={counts} statuses={statuses} />
        ) : (
          <LoadingOrNone queryResult={queryResult} />
        )}
      </td>
      <td>
        <BackfillMenu
          backfill={backfill}
          onResumeBackfill={onResumeBackfill}
          onTerminateBackfill={onTerminateBackfill}
          onShowStepStatus={onShowStepStatus}
          canCancelRuns={
            counts ? counts[RunStatus.QUEUED] > 0 || counts[RunStatus.STARTED] > 0 : false
          }
        />
      </td>
    </tr>
  );
};

const BackfillMenu = ({
  backfill,
  canCancelRuns,
  onTerminateBackfill,
  onResumeBackfill,
  onShowStepStatus,
}: {
  backfill: BackfillTableFragment;
  canCancelRuns: boolean;
  onTerminateBackfill: (backfill: BackfillTableFragment) => void;
  onResumeBackfill: (backfill: BackfillTableFragment) => void;
  onShowStepStatus: (backfill: BackfillTableFragment) => void;
}) => {
  const history = useHistory();
  const {canCancelPartitionBackfill, canLaunchPartitionBackfill} = usePermissionsDEPRECATED();
  const runsUrl = runsPathWithFilters([
    {
      token: 'tag',
      value: `dagster/backfill=${backfill.backfillId}`,
    },
  ]);

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
  statuses,
  counts,
}: {
  backfill: BackfillTableFragment;
  statuses: PartitionStatusesForBackfillFragment['results'] | null;
  counts: {[status: string]: number};
}) => {
  const history = useHistory();

  // Note: The backend reports a run status as the state of each partition, but
  // Dagit doesn't consider all run statuses (eg: "Canceling") a valid partition state.
  // Coerce the data from the backend into PartitionState, collapsing the counts.
  const partitionCounts = Object.entries(counts).reduce((partitionCounts, [runStatus, count]) => {
    const key = runStatusToPartitionState(runStatus as RunStatus);
    partitionCounts[key] = (partitionCounts[key] || 0) + count;
    return partitionCounts;
  }, {});

  return statuses ? (
    <PartitionStatus
      partitionNames={backfill.partitionNames}
      partitionStateForKey={(key) => runStatusToPartitionState(statuses[key])}
      splitPartitions={true}
      onClick={(partitionName) => {
        const entry = statuses.find((r) => r.partitionName === partitionName);
        if (entry?.runId) {
          history.push(`/runs/${entry.runId}`);
        }
      }}
    />
  ) : (
    <RunStatusTagsWithCounts
      succeededCount={partitionCounts[PartitionState.SUCCESS]}
      inProgressCount={partitionCounts[PartitionState.STARTED]}
      failedCount={partitionCounts[PartitionState.FAILURE]}
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
    if (assetSelection?.length) {
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

const BackfillRequestedRange = ({
  allPartitions,
  backfill,
  onExpand,
}: {
  backfill: BackfillTableFragment;
  allPartitions?: string[];
  onExpand: () => void;
}) => {
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <div>
        <TagButton onClick={onExpand}>
          <Tag intent="primary" interactive>
            {backfill.partitionNames.length.toLocaleString()} partitions
          </Tag>
        </TagButton>
      </div>
      {allPartitions && (
        <PartitionStatus
          small
          hideStatusTooltip
          partitionNames={allPartitions}
          partitionStateForKey={(key) =>
            backfill.partitionNames.includes(key) ? PartitionState.QUEUED : PartitionState.MISSING
          }
        />
      )}
    </Box>
  );
};

const BackfillStatusTag = ({
  backfill,
  counts,
}: {
  backfill: BackfillTableFragment;
  counts: {[status: string]: number};
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
      if (counts[RunStatus.SUCCESS] === backfill.partitionNames.length) {
        return <Tag intent="success">Completed</Tag>;
      }
      if (Array.from(inProgressStatuses).some((status) => counts[status])) {
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

export const SINGLE_BACKFILL_STATUS_COUNTS_QUERY = gql`
  query SingleBackfillCountsQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        backfillId
        partitionStatusCounts {
          runStatus
          count
        }
      }
    }
  }
`;

export const SINGLE_BACKFILL_STATUS_DETAILS_QUERY = gql`
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
