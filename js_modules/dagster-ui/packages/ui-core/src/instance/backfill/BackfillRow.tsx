import {QueryResult, gql, useLazyQuery} from '@apollo/client';
import {Box, Colors, Icon, Mono, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {BackfillActionsMenu, backfillCanCancelRuns} from './BackfillActionsMenu';
import {BackfillStatusTagForPage} from './BackfillStatusTagForPage';
import {
  SingleBackfillCountsQuery,
  SingleBackfillCountsQueryVariables,
} from './types/BackfillRow.types';
import {BackfillTableFragment} from './types/BackfillTable.types';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {RunStatus} from '../../graphql/types';
import {PartitionStatus, PartitionStatusHealthSourceOps} from '../../partitions/PartitionStatus';
import {useBlockTraceOnQueryResult} from '../../performance/TraceContext';
import {PipelineReference} from '../../pipelines/PipelineReference';
import {AssetKeyTagCollection} from '../../runs/AssetTagCollections';
import {CreatedByTagCell} from '../../runs/CreatedByTag';
import {runsPathWithFilters} from '../../runs/RunsFilterInput';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {useDelayedRowQuery} from '../../workspace/VirtualizedWorkspaceTable';
import {isThisThingAJob, useRepository} from '../../workspace/WorkspaceContext';
import {buildRepoAddress} from '../../workspace/buildRepoAddress';
import {repoAddressAsHumanString} from '../../workspace/repoAddressAsString';
import {RepoAddress} from '../../workspace/types';
import {workspacePathFromAddress, workspacePipelinePath} from '../../workspace/workspacePath';

interface BackfillRowProps {
  backfill: BackfillTableFragment;
  allPartitions?: string[];
  showBackfillTarget: boolean;
  onShowPartitionsRequested: (backfill: BackfillTableFragment) => void;
  refetch: () => void;
}

export const BackfillRow = (props: BackfillRowProps) => {
  const statusUnsupported =
    props.backfill.numPartitions === null ||
    props.backfill.partitionNames === null ||
    props.backfill.isAssetBackfill;

  if (statusUnsupported) {
    return <BackfillRowContent {...props} counts={null} statusQueryResult={null} />;
  }
  return (
    <BackfillRowLoader backfillId={props.backfill.id}>
      {(data) => <BackfillRowContent {...props} {...data} />}
    </BackfillRowLoader>
  );
};

interface LoadResult {
  counts: {[runStatus: string]: number} | null;
  statusQueryResult: QueryResult<any, any> | null;
}

export const BackfillRowLoader = (props: {
  backfillId: string;
  children: (data: LoadResult) => React.ReactNode;
}) => {
  const {backfillId} = props;

  const statusCounts = useLazyQuery<SingleBackfillCountsQuery, SingleBackfillCountsQueryVariables>(
    SINGLE_BACKFILL_STATUS_COUNTS_QUERY,
    {
      variables: {backfillId},
      notifyOnNetworkStatusChange: true,
    },
  );
  useBlockTraceOnQueryResult(statusCounts[1], 'SingleBackfillCountsQuery');

  // Note: We switch queries based on how many partitions there are to display,
  // because the detail is nice for small backfills but breaks for 100k+ partitions.
  //
  const [statusQueryFn, statusQueryResult] = statusCounts;

  useDelayedRowQuery(statusQueryFn);
  useQueryRefreshAtInterval(statusQueryResult, FIFTEEN_SECONDS);

  const {data} = statusQueryResult;
  const {counts} = React.useMemo(() => {
    if (data?.partitionBackfillOrError.__typename !== 'PartitionBackfill') {
      return {counts: null};
    }
    const counts = Object.fromEntries(
      data.partitionBackfillOrError.partitionStatusCounts.map((e) => [e.runStatus, e.count]),
    );
    return {counts};
  }, [data]);

  return props.children({counts, statusQueryResult});
};

export const BackfillRowContent = ({
  backfill,
  allPartitions,
  showBackfillTarget,
  onShowPartitionsRequested,
  refetch,
  counts,
  statusQueryResult,
}: BackfillRowProps & LoadResult) => {
  const repoAddress = backfill.partitionSet
    ? buildRepoAddress(
        backfill.partitionSet.repositoryOrigin.repositoryName,
        backfill.partitionSet.repositoryOrigin.repositoryLocationName,
      )
    : null;

  const renderBackfillStatus = () =>
    statusQueryResult?.loading ? (
      <div style={{color: Colors.textLight()}}>Loading</div>
    ) : (
      <BackfillStatusTag backfill={backfill} />
    );

  return (
    <tr>
      <td style={{width: 120}}>
        <Mono>
          <Link
            to={
              backfill.isAssetBackfill
                ? `/overview/backfills/${backfill.id}`
                : runsPathWithFilters([
                    {
                      token: 'tag',
                      value: `dagster/backfill=${backfill.id}`,
                    },
                  ])
            }
          >
            {backfill.id}
          </Link>
        </Mono>
      </td>
      <td style={{width: 220}}>
        {backfill.timestamp ? <TimestampDisplay timestamp={backfill.timestamp} /> : '-'}
      </td>
      {showBackfillTarget ? (
        <td style={{width: '20%'}}>
          <BackfillTarget backfill={backfill} repoAddress={repoAddress} />
        </td>
      ) : null}
      <td style={{width: allPartitions ? 300 : 140}}>
        <BackfillRequestedRange
          backfill={backfill}
          allPartitions={allPartitions}
          onExpand={() => onShowPartitionsRequested(backfill)}
        />
      </td>
      <td style={{width: 160}}>
        <CreatedByTagCell tags={backfill.tags} repoAddress={repoAddress} />
      </td>
      <td style={{width: 140}}>{renderBackfillStatus()}</td>
      <td>
        <BackfillActionsMenu
          backfill={backfill}
          canCancelRuns={backfillCanCancelRuns(backfill, counts)}
          refetch={refetch}
        />
      </td>
    </tr>
  );
};

const BackfillTarget = ({
  backfill,
  repoAddress,
}: {
  backfill: BackfillTableFragment;
  repoAddress: RepoAddress | null;
}) => {
  const repo = useRepository(repoAddress);
  const {assetSelection, partitionSet, partitionSetName} = backfill;

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
        <Icon name="repo" color={Colors.textLight()} />
        <Link to={workspacePathFromAddress(repoAddress)}>
          {repoAddressAsHumanString(repoAddress)}
        </Link>
      </Box>
    ) : undefined;

  const buildPipelineOrAssets = () => {
    if (assetSelection?.length) {
      return <AssetKeyTagCollection assetKeys={assetSelection} dialogTitle="Assets in backfill" />;
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

export const BackfillStatusTag = ({backfill}: {backfill: BackfillTableFragment}) => {
  return <BackfillStatusTagForPage backfill={backfill} />;
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
        id
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
        id
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
