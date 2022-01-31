import {gql, useQuery} from '@apollo/client';
import {Box, ColorsWIP, IconWIP, MetadataTable, StyledTable} from '@dagster-io/ui';
import * as React from 'react';
import {useEffect, useLayoutEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {displayNameForAssetKey} from '../../app/Util';
import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {PartitionHealthSummary} from '../../assets/PartitionHealthSummary';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {MetadataEntry, METADATA_ENTRY_FRAGMENT} from '../../runs/MetadataEntry';
import {
  isTableSchemaMetadataEntry,
  TableSchema,
  TTableSchemaMetadataEntry,
} from '../../runs/TableSchema';
import {MetadataEntryFragment} from '../../runs/types/MetadataEntryFragment';
import {RepoAddress} from '../types';

import {LiveDataForNode} from './Utils';
import {AssetGraphQuery_pipelineOrError_Pipeline_assetNodes} from './types/AssetGraphQuery';
import {
  DagsterTypeForAssetOp,
  DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_metadataEntries,
  DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type,
} from './types/DagsterTypeForAssetOp';

export type AssetType = DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type;
export type AssetMetadata = DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_metadataEntries[];

// TODO: needs to be renamed
export const extractOutputType = (result: DagsterTypeForAssetOp): AssetType | null => {
  if (result.repositoryOrError.__typename === 'Repository') {
    const outputType = result.repositoryOrError?.usedSolid?.definition.outputDefinitions[0]?.type;
    return outputType || null;
  } else {
    return null;
  }
};

export const extractOutputTableSchemaMetadataEntry = (
  result: DagsterTypeForAssetOp,
): TTableSchemaMetadataEntry | null => {
  const type = extractOutputType(result);
  // TODO don't know why this isn't working, type inference is wrong
  // const x = type.metadataEntries.find((entry) => isTableSchemaMetadataEntry(entry));
  if (type !== null) {
    for (const entry of type.metadataEntries) {
      if (isTableSchemaMetadataEntry(entry)) {
        return entry;
      }
    }
    return null;
  } else {
    return null;
  }
};

// TODO: needs to be renamed
export const extractOutputMetadata = (result: DagsterTypeForAssetOp): AssetMetadata | null => {
  if (result.repositoryOrError.__typename === 'Repository') {
    const outputType =
      result.repositoryOrError?.usedSolid?.definition.outputDefinitions[0]?.metadataEntries;
    return outputType || null;
  } else {
    return null;
  }
};

export const AssetTypeSidebarInfo: React.FC<{type: AssetType}> = ({type}) => {
  const tableSchemaEntry = type.metadataEntries.find(isTableSchemaMetadataEntry);
  return (
    <Box flex={{direction: 'column'}}>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Description description={type.description || 'No description provided'} />
      </Box>
      <Box padding={{left: 16}}>
        {tableSchemaEntry && TableSchema(tableSchemaEntry)}
      </Box>
    </Box>
  );
};

const DescriptionSidebarSection: React.FC<{
  description: string;
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  repoAddress: RepoAddress;
}> = ({description, definition, repoAddress}) => {
  const Plugin = pluginForMetadata(definition.metadata);
  return (
    <SidebarSection title="Description">
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Description description={description} />
      </Box>

      {definition.metadata && Plugin && Plugin.SidebarComponent && (
        <Plugin.SidebarComponent definition={definition} repoAddress={repoAddress} />
      )}
    </SidebarSection>
  );
};

const TypeSidebarSection: React.FC<{
  assetType: AssetType;
}> = ({assetType}) => (
  <SidebarSection title="Type">
    <AssetTypeSidebarInfo type={assetType} />
  </SidebarSection>
);

const MetadataSidebarSection: React.FC<{
  assetMetadata: AssetMetadata;
}> = ({assetMetadata}) => {
  const rows = assetMetadata.map((entry) => {
    return {
      key: entry.label,
      value: <MetadataEntry entry={entry} />,
    };
  });
  return (
    <SidebarSection title="Metadata">
      <Box padding={{vertical: 16, horizontal: 24}}>
        <MetadataTable rows={rows} />
      </Box>
    </SidebarSection>
  );
};

export const SidebarAssetInfo: React.FC<{
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes;
  liveData: LiveDataForNode;
  repoAddress: RepoAddress;
}> = ({node, definition, repoAddress, liveData}) => {
  const {lastMaterialization} = liveData || {};
  const displayName = displayNameForAssetKey(node.assetKey);

  // TODO: not sure about the fetchPolicy etc here
  const {data: dagsterTypeQueryPayload} = useQuery<DagsterTypeForAssetOp>(
    DAGSTER_TYPE_FOR_ASSET_OP_QUERY,
    {
      variables: {
        repoSelector: {
          repositoryName: repoAddress.name,
          repositoryLocationName: repoAddress.location,
        },
        assetOpName: definition.name,
      },
      fetchPolicy: 'cache-and-network',
      partialRefetch: true,
      notifyOnNetworkStatusChange: true,
    },
  );
  const [assetType, setAssetType] = useState<AssetType | null>(null);
  const [assetMetadata, setAssetMetadata] = useState<AssetMetadata | null>(null);
  useEffect(() => {
    if (dagsterTypeQueryPayload) {
      setAssetType(extractOutputType(dagsterTypeQueryPayload));
      setAssetMetadata(extractOutputMetadata(dagsterTypeQueryPayload));
    }
  }, [dagsterTypeQueryPayload]);

  return (
    <>
      <Box flex={{gap: 4, direction: 'column'}} margin={{left: 24, right: 12, vertical: 16}}>
        <SidebarTitle style={{marginBottom: 0, display: 'flex', justifyContent: 'space-between'}}>
          {displayName}
          {displayName !== node.opName ? (
            <Box style={{opacity: 0.5}} flex={{gap: 6, alignItems: 'center'}}>
              <IconWIP name="op" size={16} />
            </Box>
          ) : undefined}
        </SidebarTitle>
        <AssetCatalogLink to={`/instance/assets/${node.assetKey.path.join('/')}`}>
          {'View in Asset Catalog '}
          <IconWIP name="open_in_new" color={ColorsWIP.Link} />
        </AssetCatalogLink>
      </Box>

      {(node.description ||
        !(node.description || assetType || assetMetadata)) && (
          <DescriptionSidebarSection
            description={node.description || 'No description provided'}
            definition={definition}
            repoAddress={repoAddress}
          />
        )}

      {assetMetadata && (
        <MetadataSidebarSection assetMetadata={assetMetadata}></MetadataSidebarSection>
      )}
      {assetType && <TypeSidebarSection assetType={assetType}></TypeSidebarSection>}

      {node.partitionDefinition && (
        <SidebarSection title="Partitions">
          <Box padding={{vertical: 16, horizontal: 24}} flex={{direction: 'column', gap: 16}}>
            <p>{node.partitionDefinition}</p>
            <PartitionHealthSummary assetKey={node.assetKey} />
          </Box>
        </SidebarSection>
      )}

      <div style={{borderBottom: `2px solid ${ColorsWIP.Gray300}`}} />

      <AssetMaterializations
        assetKey={node.assetKey}
        assetLastMaterializedAt={lastMaterialization?.timestamp}
        assetHasDefinedPartitions={!!node.partitionDefinition}
        asSidebarSection
        liveData={liveData}
        paramsTimeWindowOnly={false}
        params={{}}
        setParams={() => {}}
      />
    </>
  );
};

const AssetCatalogLink = styled(Link)`
  display: flex;
  gap: 5px;
  padding: 6px;
  margin: -6px;
  align-items: center;
  white-space: nowrap;
`;

// TODO: Not sure if it's best to run a new query here or alter an upstream
// query to provide the needed info, but this will do for now.
// TODO: Need to rename this query to something that accounns for pulling output metadata
export const DAGSTER_TYPE_FOR_ASSET_OP_QUERY = gql`
  query DagsterTypeForAssetOp($repoSelector: RepositorySelector!, $assetOpName: String!) {
    repositoryOrError(repositorySelector: $repoSelector) {
      ... on Repository {
        id
        usedSolid(name: $assetOpName) {
          definition {
            outputDefinitions {
              metadataEntries {
                ...MetadataEntryFragment
              }
              type {
                ... on DagsterType {
                  name
                  description
                  metadataEntries {
                    ...MetadataEntryFragment
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  ${METADATA_ENTRY_FRAGMENT}
`;
