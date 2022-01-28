import {Box, ColorsWIP, IconWIP, StyledTable} from '@dagster-io/ui';
import styled from 'styled-components/macro';
import React from 'react';
import {Link} from 'react-router-dom';

import {displayNameForAssetKey} from '../../app/Util';
import {AssetEvents} from '../../assets/AssetEvents';
import {PartitionHealthSummary, usePartitionHealthData} from '../../assets/PartitionHealthSummary';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {buildRepoAddress} from '../buildRepoAddress';

import {LiveDataForNode} from './Utils';
import {AssetGraphQuery_assetNodes} from './types/AssetGraphQuery';
import { METADATA_ENTRY_FRAGMENT } from '../../runs/MetadataEntry';
import { gql, useQuery } from '@apollo/client';
import { SidebarAssetDetail, SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition, SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type } from './types/SidebarAssetDetail';
import { Loading } from '../../ui/Loading';
import { isTableSchemaMetadataEntry, TableSchema } from '../../runs/TableSchema';

type DagsterTypeinfo = SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type
type SolidDefinition = SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition
type AssetType = SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type

const extractOutputType = (result: SidebarAssetDetail): AssetType | null => {
  if (result.repositoryOrError.__typename === 'Repository') {
    const outputType = result.repositoryOrError?.usedSolid?.definition.outputDefinitions[0]?.type;
    return outputType || null;
  } else {
    return null;
  }
}

const AssetTypeInfoRoot = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`

const AssetTypeInfo: React.FC<{type: AssetType | null}> = ({type}) => {
  if (type) {
    const tableSchemaEntry = type.metadataEntries.find(isTableSchemaMetadataEntry);
    return <AssetTypeInfoRoot>
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Description description={type.description || 'No description provided'} />
      </Box>
      {tableSchemaEntry && TableSchema(tableSchemaEntry)}
    </AssetTypeInfoRoot>
  } else {
    return null;
  }
}
>>>>>>> 30aaa1369 ([dagit-type-metadata] table schema for assets)

export const SidebarAssetInfo: React.FC<{
  definition?: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_assetNodes;
  liveData: LiveDataForNode;
}> = ({node, definition, liveData}) => {
  const partitionHealthData = usePartitionHealthData([node.assetKey]);
  const Plugin = pluginForMetadata(definition?.metadata || []);
  const {lastMaterialization} = liveData || {};
  const displayName = displayNameForAssetKey(node.assetKey);
  const repoAddress = buildRepoAddress(node.repository.name, node.repository.location.name);

  const queryResult = useQuery<SidebarAssetDetail>(SIDEBAR_ASSET_DETAIL_QUERY, {
    variables: {
      repoSelector: { repositoryName: repoAddress.name, repositoryLocationName: repoAddress.location },
      opName: definition.name,
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

        {definition?.metadata && Plugin && Plugin.SidebarComponent && (
          <Plugin.SidebarComponent definition={definition} repoAddress={repoAddress} />
        )}
      </SidebarSection>

      {queryResult.data && (
        <SidebarSection title="Type">
          {queryResult.data && <AssetTypeInfo type={extractOutputType(queryResult.data)}/>}
        </SidebarSection>
      )}

      {node.partitionDefinition && (
        <SidebarSection title="Partitions">
          <Box padding={{vertical: 16, horizontal: 24}} flex={{direction: 'column', gap: 16}}>
            <p>{node.partitionDefinition}</p>
            <PartitionHealthSummary assetKey={node.assetKey} data={partitionHealthData} />
          </Box>
        </SidebarSection>
      )}

      <div style={{borderBottom: `2px solid ${ColorsWIP.Gray300}`}} />

      <AssetEvents
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
const SIDEBAR_ASSET_DETAIL_QUERY = gql`
  query SidebarAssetDetail($repoSelector: RepositorySelector!, $opName: String!) {
    repositoryOrError(repositorySelector: $repoSelector) {
      ... on Repository {
        id
        usedSolid(name: $opName) {
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
