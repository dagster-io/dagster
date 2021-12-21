import {gql} from '@apollo/client';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {Description} from '../pipelines/Description';
import {explorerPathToString} from '../pipelines/PipelinePathUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {IconWIP} from '../ui/Icon';
import {NonIdealState} from '../ui/NonIdealState';
import {Subheading} from '../ui/Text';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {ASSET_NODE_FRAGMENT, ASSET_NODE_LIVE_FRAGMENT} from '../workspace/asset-graph/AssetNode';
import {LiveData} from '../workspace/asset-graph/Utils';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {AssetDefinedInMultipleReposNotice} from './AssetDefinedInMultipleReposNotice';
import {AssetNodeList} from './AssetNodeList';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeDefinition: React.FC<{
  repo: DagsterRepoOption | null;
  assetNode: AssetNodeDefinitionFragment;
  liveDataByNode: LiveData;
}> = ({repo, assetNode, liveDataByNode}) => {
  const repoAddress = repo
    ? buildRepoAddress(repo.repository.name, repo.repositoryLocation.name)
    : undefined;

  if (!repoAddress) {
    return (
      <Box padding={{vertical: 20}}>
        <NonIdealState
          icon="asset"
          title="No software-defined metadata"
          description="The definition of this asset could not be found in a repository."
        />
      </Box>
    );
  }

  return (
    <>
      <AssetDefinedInMultipleReposNotice assetId={assetNode.id} loadedFromRepo={repoAddress} />

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
              maxHeight={260}
            />
          </Box>
        </Box>
        <Box
          border={{side: 'left', width: 1, color: ColorsWIP.KeylineGray}}
          style={{width: '40%', height: 330}}
          flex={{direction: 'column'}}
        >
          <Box
            padding={{vertical: 16, left: 24, right: 12}}
            flex={{justifyContent: 'space-between'}}
            border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
          >
            <Subheading>Upstream Assets ({assetNode.dependencies.length})</Subheading>
            <JobGraphLink repoAddress={repoAddress} assetNode={assetNode} direction="upstream" />
          </Box>
          <AssetNodeList
            items={assetNode.dependencies}
            liveDataByNode={liveDataByNode}
            repoAddress={repoAddress}
          />
          <Box
            padding={{vertical: 16, left: 24, right: 12}}
            flex={{justifyContent: 'space-between'}}
            border={{side: 'horizontal', width: 1, color: ColorsWIP.KeylineGray}}
          >
            <Subheading>Downstream Assets ({assetNode.dependedBy.length})</Subheading>
            <JobGraphLink repoAddress={repoAddress} assetNode={assetNode} direction="downstream" />
          </Box>
          <AssetNodeList
            items={assetNode.dependedBy}
            liveDataByNode={liveDataByNode}
            repoAddress={repoAddress}
          />
        </Box>
      </Box>
    </>
  );
};

const JobGraphLink: React.FC<{
  repoAddress: RepoAddress;
  assetNode: AssetNodeDefinitionFragment;
  direction: 'upstream' | 'downstream';
}> = ({direction, assetNode, repoAddress}) =>
  assetNode.jobName &&
  assetNode.opName &&
  (direction === 'upstream' ? assetNode.dependencies : assetNode.dependedBy).length > 0 ? (
    <Link
      to={workspacePathFromAddress(
        repoAddress,
        `/jobs/${explorerPathToString({
          pipelineName: assetNode.jobName,
          opNames: [assetNode.opName],
          opsQuery: direction === 'upstream' ? `*${assetNode.opName}` : `${assetNode.opName}*`,
        })}`,
      )}
    >
      <Box flex={{gap: 4, alignItems: 'center'}}>
        {direction === 'upstream' ? 'View upstream graph' : 'View downstream graph'}
        <IconWIP name="open_in_new" color={ColorsWIP.Link} />
      </Box>
    </Link>
  ) : null;

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    description
    opName
    jobs {
      name
      repository {
        name
        location {
          name
        }
      }
    }

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
