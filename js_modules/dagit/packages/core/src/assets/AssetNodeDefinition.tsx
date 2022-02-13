import {gql} from '@apollo/client';
import {Box, ColorsWIP, IconWIP, Caption, Subheading, Mono} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey, tokenForAssetKey} from '../app/Util';
import {Description} from '../pipelines/Description';
import {instanceAssetsExplorerPathToURL} from '../pipelines/PipelinePathUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {ASSET_NODE_FRAGMENT, ASSET_NODE_LIVE_FRAGMENT} from '../workspace/asset-graph/AssetNode';
import {LiveData, __REPOSITORY_MEGA_JOB} from '../workspace/asset-graph/Utils';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';

import {AssetDefinedInMultipleReposNotice} from './AssetDefinedInMultipleReposNotice';
import {AssetNodeList} from './AssetNodeList';
import {PartitionHealthSummary, usePartitionHealthData} from './PartitionHealthSummary';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeDefinition: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  liveDataByNode: LiveData;
}> = ({assetNode, liveDataByNode}) => {
  const partitionHealthData = usePartitionHealthData([assetNode.assetKey]);
  const repoAddress = buildRepoAddress(
    assetNode.repository.name,
    assetNode.repository.location.name,
  );

  return (
    <>
      <AssetDefinedInMultipleReposNotice assetId={assetNode.id} loadedFromRepo={repoAddress} />
      <Box flex={{direction: 'row'}}>
        <Box
          style={{flex: 1}}
          flex={{direction: 'column'}}
          border={{side: 'right', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
            flex={{justifyContent: 'space-between', gap: 8}}
          >
            <Subheading>Definition in Repository</Subheading>
            <DefinitionLocation assetNode={assetNode} repoAddress={repoAddress} />
          </Box>
          <Box padding={{vertical: 16, horizontal: 24}} style={{flex: 1}}>
            <Description
              description={assetNode.description || 'No description provided.'}
              maxHeight={260}
            />
          </Box>
          {assetNode.partitionDefinition && (
            <>
              <Box
                padding={{vertical: 16, horizontal: 24}}
                border={{side: 'horizontal', width: 1, color: ColorsWIP.KeylineGray}}
                flex={{justifyContent: 'space-between', gap: 8}}
              >
                <Subheading>Partitions</Subheading>
              </Box>
              <Box
                padding={{top: 16, horizontal: 24, bottom: 24}}
                flex={{direction: 'column', gap: 16}}
              >
                <p>{assetNode.partitionDefinition}</p>
                <PartitionHealthSummary assetKey={assetNode.assetKey} data={partitionHealthData} />
              </Box>
            </>
          )}

          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'horizontal', width: 1, color: ColorsWIP.KeylineGray}}
            flex={{justifyContent: 'space-between', gap: 8}}
          >
            <Subheading>Upstream Assets ({assetNode.dependencies.length})</Subheading>
            <JobGraphLink repoAddress={repoAddress} assetNode={assetNode} direction="upstream" />
          </Box>
          <AssetNodeList items={assetNode.dependencies} liveDataByNode={liveDataByNode} />

          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'horizontal', width: 1, color: ColorsWIP.KeylineGray}}
            flex={{justifyContent: 'space-between', gap: 8}}
          >
            <Subheading>Downstream Assets ({assetNode.dependedBy.length})</Subheading>
            <JobGraphLink repoAddress={repoAddress} assetNode={assetNode} direction="downstream" />
          </Box>
          <AssetNodeList items={assetNode.dependedBy} liveDataByNode={liveDataByNode} />
        </Box>
        <Box style={{flex: 0.5}} flex={{direction: 'column'}}></Box>
      </Box>
    </>
  );
};

const JobGraphLink: React.FC<{
  repoAddress: RepoAddress;
  assetNode: AssetNodeDefinitionFragment;
  direction: 'upstream' | 'downstream';
}> = ({direction, assetNode}) => {
  if (assetNode.jobNames.length === 0 || !assetNode.opName) {
    return null;
  }
  const populated =
    (direction === 'upstream' ? assetNode.dependencies : assetNode.dependedBy).length > 0;
  if (!populated) {
    return null;
  }

  const token = tokenForAssetKey(assetNode.assetKey);

  return (
    <Link
      to={instanceAssetsExplorerPathToURL({
        opNames: [token],
        opsQuery: direction === 'upstream' ? `*${token}` : `${token}*`,
      })}
    >
      <Box flex={{gap: 4, alignItems: 'center'}}>
        {direction === 'upstream' ? 'View upstream graph' : 'View downstream graph'}
        <IconWIP name="open_in_new" color={ColorsWIP.Link} />
      </Box>
    </Link>
  );
};

const DefinitionLocation: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  repoAddress: RepoAddress;
}> = ({assetNode, repoAddress}) => (
  <Box flex={{alignItems: 'baseline', gap: 16, wrap: 'wrap'}}>
    {assetNode.jobNames
      .filter((jobNames) => jobNames !== __REPOSITORY_MEGA_JOB)
      .map((jobName) => (
        <Mono key={jobName}>
          <PipelineReference
            isJob
            showIcon
            pipelineName={jobName}
            pipelineHrefContext={repoAddress}
          />
        </Mono>
      ))}
    {displayNameForAssetKey(assetNode.assetKey) !== assetNode.opName && (
      <Box flex={{gap: 6, alignItems: 'center'}}>
        <IconWIP name="op" size={16} />
        <Mono>{assetNode.opName}</Mono>
      </Box>
    )}

    {assetNode.jobNames.length === 0 && !assetNode.opName && (
      <Caption style={{marginTop: 2}}>Foreign Asset</Caption>
    )}
  </Box>
);

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    description
    opName
    jobNames
    repository {
      id
      name
      location {
        id
        name
      }
    }

    ...AssetNodeFragment
    ...AssetNodeLiveFragment

    dependencies {
      asset {
        id
        opName
        jobNames
        ...AssetNodeFragment
        ...AssetNodeLiveFragment
      }
    }
    dependedBy {
      asset {
        id
        opName
        jobNames
        ...AssetNodeFragment
        ...AssetNodeLiveFragment
      }
    }
  }
  ${ASSET_NODE_FRAGMENT}
  ${ASSET_NODE_LIVE_FRAGMENT}
`;
