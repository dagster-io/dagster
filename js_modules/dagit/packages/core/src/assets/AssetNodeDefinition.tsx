import {gql} from '@apollo/client';
import * as React from 'react';
import {useHistory} from 'react-router-dom';

import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {Box} from '../ui/Box';
import {ColorsWIP} from '../ui/Colors';
import {Subheading} from '../ui/Text';
import {
  AssetNode,
  ASSET_NODE_FRAGMENT,
  getNodeDimensions,
} from '../workspace/asset-graph/AssetNode';
import {assetKeyToString} from '../workspace/asset-graph/Utils';
import {AssetNodeFragment} from '../workspace/asset-graph/types/AssetNodeFragment';

import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeDefinition: React.FC<{assetNode: AssetNodeDefinitionFragment}> = ({
  assetNode,
}) => {
  return (
    <Box
      flex={{direction: 'row'}}
      border={{side: 'bottom', width: 4, color: ColorsWIP.KeylineGray}}
    >
      <Box style={{flex: 1, height: 350, minWidth: 0}} flex={{direction: 'column'}}>
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Subheading>Parent Assets ({assetNode.dependencies.length})</Subheading>
        </Box>
        <AssetList items={assetNode.dependencies} />
        <Box
          padding={{vertical: 16, horizontal: 24}}
          border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
        >
          <Subheading>Child Assets ({assetNode.dependedBy.length})</Subheading>
        </Box>
        <AssetList items={assetNode.dependedBy} />
      </Box>
      <Box style={{width: '40%'}} border={{side: 'left', width: 1, color: ColorsWIP.KeylineGray}}>
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
          <Description description={assetNode.description || 'No description provided.'} />
        </Box>
      </Box>
    </Box>
  );
};

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    ...AssetNodeFragment

    dependencies {
      asset {
        id
        ...AssetNodeFragment
      }
    }
    dependedBy {
      asset {
        id
        ...AssetNodeFragment
      }
    }
  }
  ${ASSET_NODE_FRAGMENT}
`;

const AssetList: React.FC<{
  items: {asset: AssetNodeFragment}[];
}> = ({items}) => {
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
            ...getNodeDimensions({...dep.asset, description: ''}),
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
            metadata={[]}
            selected={false}
            computeStatus={'none'}
            secondaryHighlight={false}
            repoAddress={{name: '', location: ''}}
          />
        </div>
      ))}
    </Box>
  );
};
