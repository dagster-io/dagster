import {Box, ColorsWIP, IconWIP, MetadataTable} from '@dagster-io/ui';
import * as React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {displayNameForAssetKey} from '../../app/Util';
import {AssetEvents} from '../../assets/AssetEvents';
import {PartitionHealthSummary, usePartitionHealthData} from '../../assets/PartitionHealthSummary';
import {DagsterTypeSummary} from '../../dagstertype/DagsterType';
import {DagsterTypeFragment} from '../../dagstertype/types/DagsterTypeFragment';
import {MetadataEntry} from '../../metadata/MetadataEntry';
import {MetadataEntryFragment} from '../../metadata/types/MetadataEntryFragment';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {buildRepoAddress} from '../buildRepoAddress';
import {RepoAddress} from '../types';

import {LiveDataForNode} from './Utils';
import {AssetGraphQuery_assetNodes} from './types/AssetGraphQuery';

export const SidebarAssetInfo: React.FC<{
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_assetNodes;
  liveData: LiveDataForNode;
}> = ({node, definition, liveData}) => {
  const partitionHealthData = usePartitionHealthData([node.assetKey]);
  const {lastMaterialization} = liveData || {};
  const displayName = displayNameForAssetKey(node.assetKey);
  const repoAddress = buildRepoAddress(node.repository.name, node.repository.location.name);
  const assetType = node.op?.outputDefinitions[0]?.type;
  const assetMetadata = node.op?.outputDefinitions[0]?.metadataEntries;

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

      {(node.description || !(node.description || assetType || assetMetadata)) && (
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
  assetType: DagsterTypeFragment;
}> = ({assetType}) => {
  return (
    <SidebarSection title="Type">
      <DagsterTypeSummary type={assetType} />
    </SidebarSection>
  );
};

const MetadataSidebarSection: React.FC<{
  assetMetadata: MetadataEntryFragment[];
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

const AssetCatalogLink = styled(Link)`
  display: flex;
  gap: 5px;
  padding: 6px;
  margin: -6px;
  align-items: center;
  white-space: nowrap;
`;
