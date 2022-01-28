import {Box, ColorsWIP, IconWIP, StyledTable} from '@dagster-io/ui';
import styled from 'styled-components/macro';
import React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey} from '../../app/Util';
import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {PartitionHealthSummary} from '../../assets/PartitionHealthSummary';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {RepoAddress} from '../types';

import {LiveDataForNode} from './Utils';
import {AssetGraphQuery_pipelineOrError_Pipeline_assetNodes} from './types/AssetGraphQuery';
import {METADATA_ENTRY_FRAGMENT} from '../../runs/MetadataEntry';
import {gql, useQuery} from '@apollo/client';
import {isTableSchemaMetadataEntry, TableSchema} from '../../runs/TableSchema';
import {
  DagsterTypeForAssetOp,
  DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type,
} from './types/DagsterTypeForAssetOp';

type AssetType = DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type;

// TODO: needs to be renamed
export const extractOutputType = (result: DagsterTypeForAssetOp): AssetType | null => {
  if (result.repositoryOrError.__typename === 'Repository') {
    const outputType = result.repositoryOrError?.usedSolid?.definition.outputDefinitions[0]?.type;
    return outputType || null;
  } else {
    return null;
  }
};

const AssetTypeInfoRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

export const AssetTypeInfo: React.FC<{type: AssetType | null}> = ({type}) => {
  if (type) {
    const tableSchemaEntry = type.metadataEntries.find(isTableSchemaMetadataEntry);
    return (
      <AssetTypeInfoRoot>
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={type.description || 'No description provided'} />
        </Box>
        {tableSchemaEntry && TableSchema(tableSchemaEntry)}
      </AssetTypeInfoRoot>
    );
  } else {
    return null;
  }
};

export const SidebarAssetInfo: React.FC<{
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes;
  liveData: LiveDataForNode;
  repoAddress: RepoAddress;
}> = ({node, definition, repoAddress, liveData}) => {
  const Plugin = pluginForMetadata(definition.metadata);
  const {lastMaterialization} = liveData || {};
  const displayName = displayNameForAssetKey(node.assetKey);

  // TODO: not sure about the fetchPolicy etc here
  const queryResult = useQuery<DagsterTypeForAssetOp>(DAGSTER_TYPE_FOR_ASSET_OP_QUERY, {
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
  });

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

      <SidebarSection title="Description">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Description description={node.description || 'No description provided'} />
        </Box>

        {definition.metadata && Plugin && Plugin.SidebarComponent && (
          <Plugin.SidebarComponent definition={definition} repoAddress={repoAddress} />
        )}
      </SidebarSection>

      {queryResult.data && (
        <SidebarSection title="Type">
          {queryResult.data && <AssetTypeInfo type={extractOutputType(queryResult.data)} />}
        </SidebarSection>
      )}

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
export const DAGSTER_TYPE_FOR_ASSET_OP_QUERY = gql`
  query DagsterTypeForAssetOp($repoSelector: RepositorySelector!, $assetOpName: String!) {
    repositoryOrError(repositorySelector: $repoSelector) {
      ... on Repository {
        id
        usedSolid(name: $assetOpName) {
          definition {
            outputDefinitions {
              type {
                ... on DagsterType {
                  name
                  description
                  metadataEntries {
                    label
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
