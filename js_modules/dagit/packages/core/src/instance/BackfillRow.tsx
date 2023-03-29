import {gql, QueryResult, useLazyQuery} from '@apollo/client';
import {Box, Button, Colors, Icon, MenuItem, Menu, Popover, Tag, Mono} from '@dagster-io/ui';
import countBy from 'lodash/countBy';
import * as React from 'react';
import {useHistory, Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {showCustomAlert} from '../app/CustomAlertProvider';
import {PythonErrorInfo} from '../app/PythonErrorInfo';
import {useQueryRefreshAtInterval, FIFTEEN_SECONDS} from '../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {RunStatus, BulkActionStatus} from '../graphql/types';
import {PartitionStatus, PartitionStatusHealthSourceOps} from '../partitions/PartitionStatus';
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

const NoBackfillStatusQuery = [
  () => Promise.resolve({data: undefined} as QueryResult<undefined>),
  {data: undefined, called: true, loading: false} as QueryResult<undefined>,
] as const;

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

  const statusUnsupported = backfill.numPartitions === null || backfill.partitionNames === null;

  // Note: We switch queries based on how many partitions there are to display,
  // because the detail is nice for small backfills but breaks for 100k+ partitions.
  //
  // If the number of partitions or partition names are missing, we use a mock to
  // avoid executing any query at all. This is a bit awkward, but seems cleaner than
  // making the hooks below support an optional query function / result.
  const [statusQueryFn, statusQueryResult] = statusUnsupported
    ? NoBackfillStatusQuery
    : (backfill.numPartitions || 0) > BACKFILL_PARTITIONS_COUNTS_THRESHOLD
    ? statusCounts
    : statusDetails;

  useDelayedRowQuery(statusQueryFn);
  useQueryRefreshAtInterval(statusQueryResult, FIFTEEN_SECONDS);

  const {data} = statusQueryResult;
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
        {counts || statusUnsupported ? (
          <BackfillStatusTag backfill={backfill} counts={counts} />
        ) : (
          <LoadingOrNone queryResult={statusQueryResult} noneString={'\u2013'} />
        )}
      </td>
      <td>
        {backfill.isValidSerialization ? (
          counts ? (
            <BackfillRunStatus backfill={backfill} counts={counts} statuses={statuses} />
          ) : (
            <LoadingOrNone queryResult={statusQueryResult} noneString={'\u2013'} />
          )
        ) : (
          <p>A partitions definition has changed since this backfill ran.</p>
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
  const {hasResumePermission} = backfill;

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
          {backfill.hasCancelPermission ? (
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
          {hasResumePermission &&
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
  const partitionCounts = Object.entries(counts).reduce((partitionCounts, [runStatus, count]) => {
    partitionCounts[runStatus] = (partitionCounts[runStatus] || 0) + count;
    return partitionCounts;
  }, {});

  const health: PartitionStatusHealthSourceOps = React.useMemo(
    () => ({
      runStatusForPartitionKey: (key: string) =>
        statuses?.filter((s) => s.partitionName === key)[0]?.runStatus || RunStatus.NOT_STARTED,
    }),
    [statuses],
  );

  return statuses && backfill.partitionNames ? (
    <PartitionStatus
      partitionNames={backfill.partitionNames}
      health={health}
      splitPartitions
      onClick={(partitionName) => {
        const entry = statuses.find((r) => r.partitionName === partitionName);
        if (entry?.runId) {
          history.push(`/runs/${entry.runId}`);
        }
      }}
    />
  ) : (
    <RunStatusTagsWithCounts
      succeededCount={partitionCounts[RunStatus.SUCCESS]}
      inProgressCount={partitionCounts[RunStatus.STARTED]}
      failedCount={partitionCounts[RunStatus.FAILURE]}
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
    if (partitionSetName) {
      return <span style={{fontWeight: 500}}>{partitionSetName}</span>;
    }
    return null;
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
  const {partitionNames, numPartitions} = backfill;

  if (numPartitions === null) {
    return <span />;
  }

  const numPartitionsLabel = `${numPartitions.toLocaleString()} ${
    numPartitions === 1 ? 'partition' : 'partitions'
  }`;
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      <div>
        {partitionNames ? (
          <TagButton onClick={onExpand}>
            <Tag intent="primary" interactive>
              {numPartitionsLabel}
            </Tag>
          </TagButton>
        ) : (
          <Tag intent="primary">{numPartitionsLabel}</Tag>
        )}
      </div>
      {allPartitions && partitionNames && (
        <RequestedPartitionStatusBar all={allPartitions} requested={partitionNames} />
      )}
    </Box>
  );
};

const RequestedPartitionStatusBar = ({all, requested}: {all: string[]; requested: string[]}) => {
  const health: PartitionStatusHealthSourceOps = React.useMemo(
    () => ({
      runStatusForPartitionKey: (key: string) =>
        requested && requested.includes(key) ? RunStatus.QUEUED : RunStatus.NOT_STARTED,
    }),
    [requested],
  );
  return <PartitionStatus small hideStatusTooltip partitionNames={all} health={health} />;
};

const BackfillStatusTag = ({
  backfill,
  counts,
}: {
  backfill: BackfillTableFragment;
  counts: {[status: string]: number} | null;
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
      if (backfill.partitionNames === null) {
        return <Tag intent="success">Completed</Tag>;
      }
      if (!counts) {
        return <div style={{color: Colors.Gray500}}>None</div>;
      }
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
