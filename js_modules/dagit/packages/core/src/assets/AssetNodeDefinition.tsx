import {gql} from '@apollo/client';
import {Body, Box, Caption, Colors, ConfigTypeSchema, Icon, Mono, Subheading} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {useFeatureFlags} from '../app/Flags';
import {ASSET_NODE_FRAGMENT} from '../asset-graph/AssetNode';
import {
  displayNameForAssetKey,
  isHiddenAssetGroupJob,
  LiveData,
  toGraphId,
} from '../asset-graph/Utils';
import {AssetNodeForGraphQueryFragment} from '../asset-graph/types/useAssetGraphData.types';
import {DagsterTypeSummary} from '../dagstertype/DagsterType';
import {Description} from '../pipelines/Description';
import {PipelineReference} from '../pipelines/PipelineReference';
import {ResourceContainer, ResourceHeader} from '../pipelines/SidebarOpHelpers';
import {Version} from '../versions/Version';
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
import {CurrentMinutesLateTag, freshnessPolicyDescription} from './CurrentMinutesLateTag';
import {DependsOnSelfBanner} from './DependsOnSelfBanner';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinition.types';

export const AssetNodeDefinition: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  upstream: AssetNodeForGraphQueryFragment[] | null;
  downstream: AssetNodeForGraphQueryFragment[] | null;
  liveDataByNode: LiveData;
  dependsOnSelf: boolean;
}> = ({assetNode, upstream, downstream, liveDataByNode, dependsOnSelf}) => {
  const {assetMetadata, assetType} = metadataForAssetNode(assetNode);
  const {flagSidebarResources} = useFeatureFlags();
  const liveDataForNode = liveDataByNode[toGraphId(assetNode.assetKey)];

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
        padded={true}
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
            <DescriptionAnnotations assetNode={assetNode} repoAddress={repoAddress} />
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
          {assetNode.opVersion && (
            <>
              <Box
                padding={{vertical: 16, horizontal: 24}}
                border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
              >
                <Subheading>Code version</Subheading>
              </Box>
              <Box padding={{vertical: 16, horizontal: 24}} flex={{gap: 12, alignItems: 'center'}}>
                <Version>{assetNode.opVersion}</Version>
              </Box>
            </>
          )}
          {liveDataForNode?.freshnessPolicy && (
            <>
              <Box
                padding={{vertical: 16, horizontal: 24}}
                border={{side: 'horizontal', width: 1, color: Colors.KeylineGray}}
              >
                <Subheading>Freshness Policy</Subheading>
              </Box>
              <Box padding={{vertical: 16, horizontal: 24}} flex={{gap: 12, alignItems: 'center'}}>
                <CurrentMinutesLateTag liveData={liveDataForNode} />
                <Body>{freshnessPolicyDescription(liveDataForNode.freshnessPolicy)}</Body>
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
          {dependsOnSelf && <DependsOnSelfBanner />}
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
        {assetConfigSchema || assetNode.requiredResources.length > 0 ? (
          <Box
            border={{side: 'vertical', width: 1, color: Colors.KeylineGray}}
            style={{flex: 0.5, minWidth: 0}}
            flex={{direction: 'column'}}
          >
            {assetNode.requiredResources.length > 0 && (
              <>
                <Box
                  padding={{vertical: 16, horizontal: 24}}
                  border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
                >
                  <Subheading>Required Resources</Subheading>
                </Box>
                <Box
                  padding={{vertical: 16, horizontal: 24}}
                  border={{side: 'bottom', width: 1, color: Colors.KeylineGray}}
                >
                  {assetNode.requiredResources.map((resource) => (
                    <ResourceContainer key={resource.resourceKey}>
                      <Icon name="resource" color={Colors.Gray700} />
                      {flagSidebarResources && repoAddress ? (
                        <Link
                          to={workspacePathFromAddress(
                            repoAddress,
                            `/resources/${resource.resourceKey}`,
                          )}
                        >
                          <ResourceHeader>{resource.resourceKey}</ResourceHeader>
                        </Link>
                      ) : (
                        <ResourceHeader>{resource.resourceKey}</ResourceHeader>
                      )}
                    </ResourceContainer>
                  ))}
                </Box>
              </>
            )}
            {assetConfigSchema && (
              <>
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
              </>
            )}
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
                <AssetMetadataTable
                  assetMetadata={assetMetadata}
                  repoLocation={repoAddress?.location}
                />
              </Box>
            </>
          )}
        </Box>
      </Box>
    </>
  );
};

const DescriptionAnnotations: React.FC<{
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
    {assetNode.isSource && (
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
    description
    graphName
    opNames
    opVersion
    jobNames
    partitionDefinition {
      description
    }
    repository {
      id
      name
      location {
        id
        name
      }
    }
    requiredResources {
      resourceKey
    }

    ...AssetNodeConfigFragment
    ...AssetNodeFragment
    ...AssetNodeOpMetadataFragment
  }

  ${ASSET_NODE_CONFIG_FRAGMENT}
  ${ASSET_NODE_FRAGMENT}
  ${ASSET_NODE_OP_METADATA_FRAGMENT}
`;
