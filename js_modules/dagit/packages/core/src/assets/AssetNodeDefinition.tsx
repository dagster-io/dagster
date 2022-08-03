import {gql} from '@apollo/client';
import {Box, Colors, Icon, Caption, Subheading, Mono, ConfigTypeSchema} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {ASSET_NODE_FRAGMENT} from '../asset-graph/AssetNode';
import {
  displayNameForAssetKey,
  isSourceAsset,
  LiveData,
  isHiddenAssetGroupJob,
  __ASSET_JOB_PREFIX,
} from '../asset-graph/Utils';
import {AssetGraphQuery_assetNodes} from '../asset-graph/types/AssetGraphQuery';
import {DagsterTypeSummary} from '../dagstertype/DagsterType';
import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {ASSET_NODE_CONFIG_FRAGMENT} from './AssetConfig';
import {AssetDefinedInMultipleReposNotice} from './AssetDefinedInMultipleReposNotice';
import {
  AssetMetadataTable,
  ASSET_NODE_OP_METADATA_FRAGMENT,
  metadataForAssetNode,
} from './AssetMetadata';
import {AssetNodeList} from './AssetNodeList';
import {PartitionHealthSummary, usePartitionHealthData} from './PartitionHealthSummary';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

export const AssetNodeDefinition: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  upstream: AssetGraphQuery_assetNodes[] | null;
  downstream: AssetGraphQuery_assetNodes[] | null;
  liveDataByNode: LiveData;
}> = ({assetNode, upstream, downstream, liveDataByNode}) => {
  const partitionHealthData = usePartitionHealthData([assetNode.assetKey]);
  const {assetMetadata, assetType} = metadataForAssetNode(assetNode);

  const assetConfigSchema = assetNode.configField?.configType;
  const repoAddress = buildRepoAddress(
    assetNode.repository.name,
    assetNode.repository.location.name,
  );

  return (
    <>
      <AssetDefinedInMultipleReposNotice
        assetKey={assetNode.assetKey}
        loadedFromRepo={repoAddress}
      />
      <Box flex={{direction: 'row'}} style={{flex: 1}}>
        <Box
          style={{flex: 1, minWidth: 0}}
          flex={{direction: 'column'}}
          border={{side: 'right', width: 1, color: Colors.KeylineGray}}
        >
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
            flex={{justifyContent: 'space-between', gap: 8}}
          >
            <Subheading>Description</Subheading>
            <DefinitionLocation assetNode={assetNode} repoAddress={repoAddress} />
          </Box>
          <Box
            padding={{vertical: 16, horizontal: 24}}
            style={{flex: 1, flexBasis: 'content', flexGrow: 0, minHeight: 120}}
          >
            <Description
              description={assetNode.description || 'No description provided.'}
              maxHeight={260}
            />
          </Box>
          {assetNode.partitionDefinition && (
            <>
              <Box
                padding={{vertical: 16, horizontal: 24}}
                border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
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
            border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
            flex={{justifyContent: 'space-between', gap: 8}}
          >
            <Subheading>
              Upstream Assets{upstream?.length ? ` (${upstream.length})` : ''}
            </Subheading>
            <Link to="?view=lineage&lineageScope=upstream">
              <Box flex={{gap: 4, alignItems: 'center'}}>
                View upstream graph
                <Icon name="open_in_new" color={Colors.Link} />
              </Box>
            </Link>
          </Box>
          <AssetNodeList items={upstream} liveDataByNode={liveDataByNode} />
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
            flex={{justifyContent: 'space-between', gap: 8}}
          >
            <Subheading>
              Downstream Assets{downstream?.length ? ` (${downstream.length})` : ''}
            </Subheading>
            <Link to="?view=lineage&lineageScope=downstream">
              <Box flex={{gap: 4, alignItems: 'center'}}>
                View downstream graph
                <Icon name="open_in_new" color={Colors.Link} />
              </Box>
            </Link>
          </Box>
          <AssetNodeList items={downstream} liveDataByNode={liveDataByNode} />
          {/** Ensures the line between the left and right columns goes to the bottom of the page */}
          <div style={{flex: 1}} />
        </Box>
        {assetConfigSchema ? (
          <Box
            border={{side: 'vertical', width: 1, color: Colors.KeylineGray}}
            style={{flex: 0.5, minWidth: 0}}
            flex={{direction: 'column'}}
          >
            <Box
              padding={{vertical: 16, horizontal: 24}}
              border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
            >
              <Subheading>Config</Subheading>
            </Box>
            <Box padding={{vertical: 16, horizontal: 24}}>
              <ConfigTypeSchema
                type={assetConfigSchema}
                typesInScope={assetConfigSchema.recursiveConfigTypes}
              />
            </Box>
          </Box>
        ) : null}

        <Box style={{flex: 0.5, minWidth: 0}} flex={{direction: 'column'}}>
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
          >
            <Subheading>Type</Subheading>
          </Box>
          {assetType ? (
            <DagsterTypeSummary type={assetType} />
          ) : (
            <Box padding={{vertical: 16, horizontal: 24}}>
              <Description description="No type data provided." />
            </Box>
          )}
          {assetMetadata.length > 0 && (
            <>
              <Box
                padding={{vertical: 16, horizontal: 24}}
                border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
                flex={{justifyContent: 'space-between', gap: 8}}
              >
                <Subheading>Metadata</Subheading>
              </Box>
              <Box style={{flex: 1}}>
                <AssetMetadataTable assetMetadata={assetMetadata} />
              </Box>
            </>
          )}
        </Box>
      </Box>
    </>
  );
};

const DefinitionLocation: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  repoAddress: RepoAddress;
}> = ({assetNode, repoAddress}) => (
  <Box flex={{alignItems: 'baseline', gap: 16, wrap: 'wrap'}} style={{lineHeight: 0}}>
    {assetNode.jobNames
      .filter((jobName) => !isHiddenAssetGroupJob(jobName))
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
    <OpNamesDisplay assetNode={assetNode} repoAddress={repoAddress} />
    {isSourceAsset(assetNode) && (
      <Caption style={{lineHeight: '16px', marginTop: 2}}>Source Asset</Caption>
    )}
  </Box>
);

const OpNamesDisplay = (props: {
  assetNode: AssetNodeDefinitionFragment;
  repoAddress: RepoAddress;
}) => {
  const {assetNode, repoAddress} = props;
  const {assetKey, graphName, opNames, jobNames} = assetNode;
  const opCount = opNames.length;

  if (!opCount) {
    return null;
  }

  if (!graphName) {
    const firstOp = opNames[0];
    if (displayNameForAssetKey(assetKey) === firstOp) {
      return null;
    }
    const opPath = workspacePathFromAddress(repoAddress, `/ops/${firstOp}`);
    return (
      <Box flex={{gap: 4, alignItems: 'center'}}>
        <Icon name="op" size={16} />
        <Mono>
          <Link to={opPath}>{firstOp}</Link>
        </Mono>
      </Box>
    );
  }

  if (!jobNames.length) {
    return null;
  }

  return (
    <Box flex={{gap: 4, alignItems: 'center'}}>
      <Icon name="schema" size={16} />
      <Mono>
        <Link to={workspacePathFromAddress(repoAddress, `/graphs/${jobNames[0]}/${graphName}/`)}>
          {graphName}
        </Link>
        {` (${opCount === 1 ? '1 op' : `${opCount} ops`})`}
      </Mono>
    </Box>
  );
};

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    ...AssetNodeConfigFragment
    description
    graphName
    opNames
    jobNames
    partitionDefinition
    repository {
      id
      name
      location {
        id
        name
      }
    }
    ...AssetNodeFragment
    ...AssetNodeOpMetadataFragment
  }
  ${ASSET_NODE_CONFIG_FRAGMENT}
  ${ASSET_NODE_FRAGMENT}
  ${ASSET_NODE_OP_METADATA_FRAGMENT}
`;
