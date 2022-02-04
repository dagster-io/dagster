import {gql, useQuery} from '@apollo/client';
import {Box, ColorsWIP, IconWIP, Caption, Subheading, Mono, MetadataTable} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey, tokenForAssetKey} from '../app/Util';
import {MetadataEntry} from '../metadata/MetadataEntry';
import {TableSchema, ITableSchemaMetadataEntry} from '../metadata/TableSchema';
import {Description} from '../pipelines/Description';
import {explorerPathToString} from '../pipelines/PipelinePathUtils';
import {PipelineReference} from '../pipelines/PipelineReference';
import {ASSET_NODE_FRAGMENT, ASSET_NODE_LIVE_FRAGMENT} from '../workspace/asset-graph/AssetNode';
import {
  AssetTypeSidebarInfo,
  DAGSTER_TYPE_FOR_ASSET_OP_QUERY,
  extractOutputType,
  extractOutputMetadata,
  AssetMetadata,
  AssetType,
  extractOutputTableSchemaMetadataEntry,
} from '../workspace/asset-graph/SidebarAssetInfo';
import {LiveData} from '../workspace/asset-graph/Utils';
import {DagsterTypeForAssetOp} from '../workspace/asset-graph/types/DagsterTypeForAssetOp';
import {buildRepoAddress} from '../workspace/buildRepoAddress';
import {RepoAddress} from '../workspace/types';
import {workspacePathFromAddress} from '../workspace/workspacePath';

import {AssetDefinedInMultipleReposNotice} from './AssetDefinedInMultipleReposNotice';
import {AssetNodeList} from './AssetNodeList';
import {PartitionHealthSummary, usePartitionHealthData} from './PartitionHealthSummary';
import {AssetNodeDefinitionFragment} from './types/AssetNodeDefinitionFragment';

const AssetMetadataTable: React.FC<{
  assetMetadata: AssetMetadata;
}> = ({assetMetadata}) => {
  const rows = assetMetadata.map((entry) => {
    return {
      key: entry.label,
      value: <MetadataEntry entry={entry} />,
    };
  });
  return (
    <Box padding={{vertical: 16, horizontal: 24}}>
      <MetadataTable rows={rows} />
    </Box>
  );
};

export const AssetNodeDefinition: React.FC<{
  assetNode: AssetNodeDefinitionFragment;
  liveDataByNode: LiveData;
}> = ({assetNode, liveDataByNode}) => {
  const partitionHealthData = usePartitionHealthData([assetNode.assetKey]);
  const repoAddress = buildRepoAddress(
    assetNode.repository.name,
    assetNode.repository.location.name,
  );
  const {data: dagsterTypeQueryPayload} = useQuery<DagsterTypeForAssetOp>(
    DAGSTER_TYPE_FOR_ASSET_OP_QUERY,
    {
      variables: {
        repoSelector: {
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
        },
        assetOpName: assetNode.opName,
      },
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      notifyOnNetworkStatusChange: true,
    },
  );
  const [assetType, setAssetType] = React.useState<AssetType | null>(null);
  const [
    assetTableSchemaMetadataEntry,
    setAssetTableSchemaMetadataEntry,
  ] = React.useState<ITableSchemaMetadataEntry | null>(null);
  const [assetMetadata, setAssetMetadata] = React.useState<AssetMetadata | null>(null);
  React.useEffect(() => {
    if (dagsterTypeQueryPayload) {
      setAssetType(extractOutputType(dagsterTypeQueryPayload));
      setAssetTableSchemaMetadataEntry(
        extractOutputTableSchemaMetadataEntry(dagsterTypeQueryPayload),
      );
      setAssetMetadata(extractOutputMetadata(dagsterTypeQueryPayload));
    }
  }, [dagsterTypeQueryPayload]);

  return (
    <>
      <AssetDefinedInMultipleReposNotice assetId={assetNode.id} loadedFromRepo={repoAddress} />
      <Box
        flex={{direction: 'row'}}
        border={{side: 'bottom', width: 4, color: ColorsWIP.KeylineGray}}
      >
        <Box style={{flex: 1}} flex={{direction: 'column'}}>
          <Box
            padding={{vertical: 16, horizontal: 24}}
            border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
            flex={{justifyContent: 'space-between', gap: 8}}
          >
            <Subheading>Definition in Repository</Subheading>
            {/* Need a better way than height 0 to prevent PipelineReference from being too tall */}
            <Box flex={{alignItems: 'baseline', gap: 16, wrap: 'wrap'}} style={{height: 0}}>
              {assetNode.jobs.map((job) => (
                <Mono key={job.id}>
                  <PipelineReference
                    isJob
                    showIcon
                    pipelineName={job.name}
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

              {assetNode.jobs.length === 0 && !assetNode.opName && (
                <Caption style={{marginTop: 2}}>Foreign Asset</Caption>
              )}
            </Box>
          </Box>
          <Box padding={{top: 16, horizontal: 24, bottom: 16}} style={{minHeight: 112}}>
            <Description
              description={assetNode.description || 'No description provided.'}
              maxHeight={260}
            />
          </Box>
          {assetMetadata && (
            <>
              <Box
                padding={{vertical: 16, horizontal: 24}}
                border={{side: 'horizontal', width: 1, color: ColorsWIP.KeylineGray}}
                flex={{justifyContent: 'space-between', gap: 8}}
              >
                <Subheading>Metadata</Subheading>
              </Box>
              <Box padding={{top: 16, bottom: 4}} style={{flex: 1}}>
                <AssetMetadataTable assetMetadata={assetMetadata} />
              </Box>
            </>
          )}
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
        </Box>
        {assetType && (
          <Box
            // padding={{vertical: 16, horizontal: 24}}
            border={{side: 'left', width: 1, color: ColorsWIP.KeylineGray}}
            flex={{direction: 'column'}}
          >
            <Box
              padding={{vertical: 16, left: 24, right: 12}}
              border={{side: 'bottom', width: 1, color: ColorsWIP.KeylineGray}}
            >
              <Subheading>Type</Subheading>
            </Box>
            {assetType.description && (
              <Box padding={{top: 16, horizontal: 16, bottom: 16}} style={{flex: 1}}>
                <Description
                  description={assetType.description || 'No description provided.'}
                  maxHeight={260}
                />
              </Box>
            )}
            {assetTableSchemaMetadataEntry && (
              <Box padding={{horizontal: 8, bottom: 8}}>
                <TableSchema schema={assetTableSchemaMetadataEntry.schema} />
              </Box>
            )}
          </Box>
        )}
        <Box
          border={{side: 'left', width: 1, color: ColorsWIP.KeylineGray}}
          style={{width: '40%'}}
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
          <AssetNodeList items={assetNode.dependencies} liveDataByNode={liveDataByNode} />
          <Box
            padding={{vertical: 16, left: 24, right: 12}}
            flex={{justifyContent: 'space-between'}}
            border={{side: 'horizontal', width: 1, color: ColorsWIP.KeylineGray}}
          >
            <Subheading>Downstream Assets ({assetNode.dependedBy.length})</Subheading>
            <JobGraphLink repoAddress={repoAddress} assetNode={assetNode} direction="downstream" />
          </Box>
          <AssetNodeList items={assetNode.dependedBy} liveDataByNode={liveDataByNode} />
        </Box>
      </Box>
    </>
  );
};

const JobGraphLink: React.FC<{
  repoAddress: RepoAddress;
  assetNode: AssetNodeDefinitionFragment;
  direction: 'upstream' | 'downstream';
}> = ({direction, assetNode, repoAddress}) => {
  if (assetNode.jobs.length === 0 || !assetNode.opName) {
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
      to={workspacePathFromAddress(
        repoAddress,
        `/jobs/${explorerPathToString({
          pipelineName: assetNode.jobs[0].name,
          opNames: [token],
          opsQuery: direction === 'upstream' ? `*${token}` : `${token}*`,
        })}`,
      )}
    >
      <Box flex={{gap: 4, alignItems: 'center'}}>
        {direction === 'upstream' ? 'View upstream graph' : 'View downstream graph'}
        <IconWIP name="open_in_new" color={ColorsWIP.Link} />
      </Box>
    </Link>
  );
};

export const ASSET_NODE_DEFINITION_FRAGMENT = gql`
  fragment AssetNodeDefinitionFragment on AssetNode {
    id
    description
    opName
    jobs {
      id
      name
    }
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
        jobs {
          id
          name
        }
        ...AssetNodeFragment
        ...AssetNodeLiveFragment
      }
    }
    dependedBy {
      asset {
        id
        opName
        jobs {
          id
          name
        }
        ...AssetNodeFragment
        ...AssetNodeLiveFragment
      }
    }
  }
  ${ASSET_NODE_FRAGMENT}
  ${ASSET_NODE_LIVE_FRAGMENT}
`;
