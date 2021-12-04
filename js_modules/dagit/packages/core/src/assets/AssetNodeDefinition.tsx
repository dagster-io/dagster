import {gql} from '@apollo/client';
import * as React from 'react';

import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {NonIdealState} from '../ui/NonIdealState';
import {Subheading} from '../ui/Text';
import {DagsterRepoOption} from '../workspace/WorkspaceContext';
import {ASSET_NODE_FRAGMENT, ASSET_NODE_LIVE_FRAGMENT} from '../workspace/asset-graph/AssetNode';
import {LiveData} from '../workspace/asset-graph/Utils';

import {AssetNeighborsGraph} from './AssetNeighborsGraph';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeDefinition: React.FC<{
  repo: DagsterRepoOption | null;
  assetNode: AssetNodeDefinitionFragment;
  liveDataByNode: LiveData;
}> = ({repo, assetNode, liveDataByNode}) => {
  if (!repo) {
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
            maxHeight={318}
          />
        </Box>
      </Box>
      <Box
        border={{side: 'left', width: 1, color: ColorsWIP.KeylineGray}}
        style={{width: '40%', height: 390}}
        flex={{direction: 'column'}}
      >
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Subheading>Related Assets</Subheading>
        </Box>
        <Box margin={{vertical: 16, horizontal: 24}} style={{minHeight: 0, height: '100%'}}>
          <AssetNeighborsGraph
            assetNode={assetNode}
            liveDataByNode={liveDataByNode}
            repoAddress={{name: repo.repository.name, location: repo.repositoryLocation.name}}
          />
        </Box>
      </Box>
    </Box>
  );
};

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
