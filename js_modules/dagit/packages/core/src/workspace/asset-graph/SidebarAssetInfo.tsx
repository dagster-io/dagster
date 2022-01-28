import {Box, ColorsWIP, IconWIP} from '@dagster-io/ui';
import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {displayNameForAssetKey} from '../../app/Util';
import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {PartitionHealthSummary} from '../../assets/PartitionHealthSummary';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {buildRepoAddress} from '../buildRepoAddress';

import {LiveDataForNode} from './Utils';
import {AssetGraphQuery_assetNodes} from './types/AssetGraphQuery';

export const SidebarAssetInfo: React.FC<{
  definition?: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_assetNodes;
  liveData: LiveDataForNode;
}> = ({node, definition, liveData}) => {
  const Plugin = pluginForMetadata(definition?.metadata || []);
  const {lastMaterialization} = liveData || {};
  const displayName = displayNameForAssetKey(node.assetKey);
  const repoAddress = buildRepoAddress(node.repository.name, node.repository.location.name);
  return (
    <>
      <Box flex={{gap: 4, direction: 'column'}} margin={{left: 24, right: 12, vertical: 16}}>
        <SidebarTitle style={{marginBottom: 0, display: 'flex', justifyContent: 'space-between'}}>
          {displayName}
          {displayName !== node.opName ? (
            <Box style={{opacity: 0.5}} flex={{gap: 6, alignItems: 'center'}}>
              <IconWIP name="op" size={16} />
              {node.opName}
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
