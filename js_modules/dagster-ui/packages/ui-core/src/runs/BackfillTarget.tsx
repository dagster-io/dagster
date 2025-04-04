import {Box, Colors, Icon, Tag} from '@dagster-io/ui-components';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components';

import {gql} from '../apollo-client';
import {AssetKeyTagCollection} from './AssetTagCollections';
import {isHiddenAssetGroupJob} from '../asset-graph/Utils';
import {PartitionBackfill, RunStatus} from '../graphql/types';
import {PartitionStatus, PartitionStatusHealthSourceOps} from '../partitions/PartitionStatus';
import {PipelineReference, PipelineTag} from '../pipelines/PipelineReference';
import {isThisThingAJob, useRepository} from '../workspace/WorkspaceContext/util';
import {repoAddressAsHumanString} from '../workspace/repoAddressAsString';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress, workspacePipelinePath} from '../workspace/workspacePath';
import {BackfillTargetFragment} from './types/BackfillTarget.types';

export const BackfillTarget = ({
  backfill,
  repoAddress,
  useTags,
  onShowPartitions,
}: {
  backfill: BackfillTargetFragment;
  repoAddress: RepoAddress | null;
  useTags: boolean;
  onShowPartitions?: () => void;
}) => {
  const repo = useRepository(repoAddress);
  const {assetSelection, partitionSet, partitionSetName} = backfill;

  const isHiddenAssetPartitionSet = isHiddenAssetGroupJob(partitionSetName || '');

  const buildHeader = () => {
    if (isHiddenAssetPartitionSet) {
      return null;
    }
    if (partitionSet && repo) {
      const link = workspacePipelinePath({
        repoName: partitionSet.repositoryOrigin.repositoryName,
        repoLocation: partitionSet.repositoryOrigin.repositoryLocationName,
        pipelineName: partitionSet.pipelineName,
        isJob: isThisThingAJob(repo, partitionSet.pipelineName),
        path: `/partitions?partitionSet=${encodeURIComponent(partitionSet.name)}`,
      });
      if (useTags) {
        return (
          <Tag icon="partition_set">
            <Link to={link}>{partitionSet.name}</Link>
          </Tag>
        );
      }
      return (
        <Link style={{fontWeight: 500}} to={link}>
          {partitionSet.name}
        </Link>
      );
    }
    if (partitionSetName) {
      if (useTags) {
        return <Tag icon="partition_set">{partitionSetName}</Tag>;
      }
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
      return (
        <AssetKeyTagCollection
          assetKeys={assetSelection}
          dialogTitle="Assets in backfill"
          useTags={useTags}
          maxRows={2}
        />
      );
    }
    if (partitionSet && repo) {
      return useTags ? (
        <PipelineTag
          showIcon
          size="small"
          pipelineName={partitionSet.pipelineName}
          pipelineHrefContext={{
            name: partitionSet.repositoryOrigin.repositoryName,
            location: partitionSet.repositoryOrigin.repositoryLocationName,
          }}
          isJob={isThisThingAJob(repo, partitionSet.pipelineName)}
        />
      ) : (
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

  const buildPartitionTag = () => {
    if (!useTags || !onShowPartitions) {
      return null;
    }
    return <BackfillRequestedRange backfill={backfill} onExpand={onShowPartitions} />;
  };

  const repoLink = buildRepoLink();
  const pipelineOrAssets = buildPipelineOrAssets();
  return (
    <Box flex={{direction: 'column', gap: 8, alignItems: 'start'}}>
      <Box flex={{direction: 'row', gap: 4}}>
        {buildPartitionTag()}
        {buildHeader()}
      </Box>
      {(pipelineOrAssets || repoLink) && (
        <Box flex={{direction: 'column', gap: 4}} style={{fontSize: '12px'}}>
          {repoLink && useTags ? <Tag>{repoLink}</Tag> : repoLink}
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
  backfill: Pick<PartitionBackfill, 'numPartitions' | 'partitionNames'>;
  allPartitions?: string[];
  onExpand: () => void;
}) => {
  const {partitionNames, numPartitions} = backfill;

  if (numPartitions === null || numPartitions === 0) {
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
  const health: PartitionStatusHealthSourceOps = React.useMemo(() => {
    const requestedSet = new Set(requested);
    return {
      runStatusForPartitionKey: (key: string) =>
        requestedSet.has(key) ? RunStatus.QUEUED : RunStatus.NOT_STARTED,
    };
  }, [requested]);
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

export const BACKFILL_TARGET_FRAGMENT = gql`
  fragment BackfillTargetFragment on PartitionBackfill {
    id
    partitionNames
    assetSelection {
      path
    }
    numPartitions
    partitionSetName
    partitionSet {
      name
      pipelineName
      repositoryOrigin {
        repositoryName
        repositoryLocationName
      }
    }
  }
`;
