import {gql, useQuery} from '@apollo/client';
import * as React from 'react';
import {useHistory} from 'react-router-dom';

import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Subheading} from '../ui/Text';
import {useRepositoryOptions} from '../workspace/WorkspaceContext';
import {
  AssetNode,
  ASSET_NODE_FRAGMENT,
  ASSET_NODE_LIVE_FRAGMENT,
} from '../workspace/asset-graph/AssetNode';
import {
  assetKeyToString,
  buildGraphDataFromSingleNode,
  buildLiveData,
  LiveData,
} from '../workspace/asset-graph/Utils';
import {AssetNodeFragment} from '../workspace/asset-graph/types/AssetNodeFragment';
import {findRepoContainingPipeline} from '../workspace/findRepoContainingPipeline';

import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';
import {
  AssetNodeDefinitionRunsQuery,
  AssetNodeDefinitionRunsQueryVariables,
} from './types/AssetNodeDefinitionRunsQuery';

export const AssetNodeDefinition: React.FC<{assetNode: AssetNodeDefinitionFragment}> = ({
  assetNode,
}) => {
  const {options} = useRepositoryOptions();
  const repos = assetNode.jobName ? findRepoContainingPipeline(options, assetNode.jobName) : [];

  const liveResult = useQuery<AssetNodeDefinitionRunsQuery, AssetNodeDefinitionRunsQueryVariables>(
    ASSET_NODE_DEFINITION_RUNS_QUERY,
    {
      skip: !assetNode.jobName || !repos.length,
      variables: {
        pipelineSelector: {
          pipelineName: assetNode.jobName || '',
          repositoryLocationName: repos[0].repositoryLocation.name,
          repositoryName: repos[0].repository.name,
        },
        repositorySelector: {
          repositoryLocationName: repos[0].repositoryLocation.name,
          repositoryName: repos[0].repository.name,
        },
      },
      notifyOnNetworkStatusChange: true,
      pollInterval: 5 * 1000,
    },
  );

  const inProgress =
    liveResult.data?.repositoryOrError.__typename === 'Repository'
      ? liveResult.data.repositoryOrError.inProgressRunsByStep
      : [];
  const nodesWithLatestMaterialization = [
    assetNode,
    ...assetNode.dependencies.map((d) => d.asset),
    ...assetNode.dependedBy.map((d) => d.asset),
  ];
  const liveDataByNode = buildLiveData(
    buildGraphDataFromSingleNode(assetNode),
    nodesWithLatestMaterialization,
    inProgress,
  );

  return (
    <Box
      flex={{direction: 'row'}}
      border={{side: 'bottom', width: 4, color: ColorsWIP.KeylineGray}}
    >
      <Box style={{flex: 1}}>
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
          flex={{justifyContent: 'space-between'}}
        >
          <Subheading>Definition in Repository</Subheading>
          {assetNode.jobName && (
            <PipelineReference
              showIcon
              pipelineName={assetNode.jobName}
              pipelineHrefContext={'repo-unknown'}
              isJob
            />
          )}
        </Box>
        <Box padding={{top: 16, horizontal: 24, bottom: 4}}>
          <Description
            description={assetNode.description || 'No description provided.'}
            maxHeight={278}
          />
        </Box>
      </Box>
      <Box
        style={{width: '40%', height: 350, minWidth: 0}}
        flex={{direction: 'column'}}
        border={{side: 'left', width: 1, color: ColorsWIP.KeylineGray}}
      >
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Subheading>Upstream Assets ({assetNode.dependencies.length})</Subheading>
        </Box>
        <AssetList items={assetNode.dependencies} liveDataByNode={liveDataByNode} />
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Subheading>Downstream Assets ({assetNode.dependedBy.length})</Subheading>
        </Box>
        <AssetList items={assetNode.dependedBy} liveDataByNode={liveDataByNode} />
      </Box>
    </Box>
  );
};

const ASSET_NODE_DEFINITION_RUNS_QUERY = gql`
  query AssetNodeDefinitionRunsQuery(
    $pipelineSelector: PipelineSelector!
    $repositorySelector: RepositorySelector!
  ) {
    repositoryOrError(repositorySelector: $repositorySelector) {
      __typename
      ... on Repository {
        id
        name
        inProgressRunsByStep {
          stepKey
          runs {
            id
            runId
          }
        }
      }
    }
  }
`;

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    ...AssetNodeFragment
    ...AssetNodeLiveFragment

    dependencies {
      asset {
        id
        opName
        ...AssetNodeFragment
        ...AssetNodeLiveFragment
      }
    }
    dependedBy {
      asset {
        id
        opName
        ...AssetNodeFragment
        ...AssetNodeLiveFragment
      }
    }
  }
  ${ASSET_NODE_FRAGMENT}
  ${ASSET_NODE_LIVE_FRAGMENT}
`;

const AssetList: React.FC<{
  items: {asset: AssetNodeFragment}[];
  liveDataByNode: LiveData;
}> = ({items, liveDataByNode}) => {
  const history = useHistory();

  return (
    <Box
      padding={{horizontal: 16}}
      style={{overflowX: 'auto', whiteSpace: 'nowrap', height: 120, minWidth: 0}}
    >
      {items.map((dep) => (
        <div
          style={{
            position: 'relative',
            display: 'inline-block',
            verticalAlign: 'top',
            height: 95,
            width: 215,
          }}
          key={assetKeyToString(dep.asset.assetKey)}
          onClick={(e) => {
            if (e.isDefaultPrevented()) {
              return;
            }
            history.push(`/instance/assets/${assetKeyToString(dep.asset.assetKey)}`);
          }}
        >
          <AssetNode
            definition={{...dep.asset, description: ''}}
            liveData={liveDataByNode[dep.asset.id]}
            metadata={[]}
            selected={false}
            secondaryHighlight={false}
            repoAddress={{name: '', location: ''}}
          />
        </div>
      ))}
    </Box>
  );
};
