import {Box, Colors, Icon, Mono, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {BackfillActionsMenu, backfillCanCancelRuns} from './BackfillActionsMenu';
import {BackfillStatusTagForPage} from './BackfillStatusTagForPage';
import {SingleBackfillQuery, SingleBackfillQueryVariables} from './types/BackfillRow.types';
import {BackfillTableFragment} from './types/BackfillTable.types';
import {QueryResult, gql, useLazyQuery} from '../../apollo-client';
import {FIFTEEN_SECONDS, useQueryRefreshAtInterval} from '../../app/QueryRefresh';
import {isHiddenAssetGroupJob} from '../../asset-graph/Utils';
import {RunStatus} from '../../graphql/types';
import {PartitionStatus, PartitionStatusHealthSourceOps} from '../../partitions/PartitionStatus';
import {PipelineReference} from '../../pipelines/PipelineReference';
import {AssetKeyTagCollection} from '../../runs/AssetTagCollections';
import {CreatedByTagCell} from '../../runs/CreatedByTag';
import {getBackfillPath} from '../../runs/RunsFeedUtils';
import {TimestampDisplay} from '../../schedules/TimestampDisplay';
import {useDelayedRowQuery} from '../../workspace/VirtualizedWorkspaceTable';
import {isThisThingAJob, useRepository} from '../../workspace/WorkspaceContext/util';
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
    return <BackfillRowContent {...props} hasCancelableRuns={false} statusQueryResult={null} />;
  }
  return (
    <BackfillRowLoader backfillId={props.backfill.id}>
      {(data) => <BackfillRowContent {...props} {...data} />}
    </BackfillRowLoader>
  );
};

interface LoadResult {
  hasCancelableRuns: boolean;
  statusQueryResult: QueryResult<any, any> | null;
}

export const BackfillRowLoader = (props: {
  backfillId: string;
  children: (data: LoadResult) => React.ReactNode;
}) => {
  const {backfillId} = props;

  const cancelableRuns = useLazyQuery<SingleBackfillQuery, SingleBackfillQueryVariables>(
    SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY,
    {
      variables: {backfillId},
      notifyOnNetworkStatusChange: true,
    },
  );

  const [statusQueryFn, statusQueryResult] = cancelableRuns;

  useDelayedRowQuery(statusQueryFn);
  useQueryRefreshAtInterval(statusQueryResult, FIFTEEN_SECONDS);

  const {data} = statusQueryResult;
  const {hasCancelableRuns} = React.useMemo(() => {
    if (data?.partitionBackfillOrError.__typename === 'PartitionBackfill') {
      return {hasCancelableRuns: data.partitionBackfillOrError.cancelableRuns.length > 0};
    }
    return {hasCancelableRuns: false};
  }, [data]);

  return props.children({hasCancelableRuns, statusQueryResult});
};

export const BackfillRowContent = ({
  backfill,
  allPartitions,
  showBackfillTarget,
  onShowPartitionsRequested,
  refetch,
  hasCancelableRuns,
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
      <BackfillStatusTagForPage backfill={backfill} />
    );

  return (
    <tr>
      <td style={{width: 120}}>
        <Mono>
          <Link to={getBackfillPath(backfill.id, backfill.isAssetBackfill)}>{backfill.id}</Link>
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
          canCancelRuns={backfillCanCancelRuns(backfill, hasCancelableRuns)}
          refetch={refetch}
        />
      </td>
    </tr>
  );
};

export const BackfillTarget = ({
  backfill,
  repoAddress,
}: {
  backfill: Pick<BackfillTableFragment, 'assetSelection' | 'partitionSet' | 'partitionSetName'>;
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

  const repoLink = buildRepoLink();
  const pipelineOrAssets = buildPipelineOrAssets();
  return (
    <Box flex={{direction: 'column', gap: 8}}>
      {buildHeader()}
      {(pipelineOrAssets || repoLink) && (
        <Box flex={{direction: 'column', gap: 4}} style={{fontSize: '12px'}}>
          {repoLink}
          {pipelineOrAssets}
        </Box>
      )}
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

export const SINGLE_BACKFILL_CANCELABLE_RUNS_QUERY = gql`
  query SingleBackfillQuery($backfillId: String!) {
    partitionBackfillOrError(backfillId: $backfillId) {
      ... on PartitionBackfill {
        id
        cancelableRuns {
          id
          runId
          status
        }
      }
    }
  }
`;
