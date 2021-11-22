import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {LatestMaterializationMetadata} from '../../assets/LastMaterializationMetadata';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {Box} from '../../ui/Box';
import {ColorsWIP} from '../../ui/Colors';
import {IconWIP} from '../../ui/Icon';
import {RepoAddress} from '../types';

import {assetKeyToString} from './Utils';
import {AssetGraphQuery_repositoryOrError_Repository_assetNodes} from './types/AssetGraphQuery';

export const SidebarAssetInfo: React.FC<{
  node: AssetGraphQuery_repositoryOrError_Repository_assetNodes;
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  repoAddress: RepoAddress;
}> = ({node, definition, repoAddress}) => {
  const Plugin = pluginForMetadata(definition.metadata);

  return (
    <div style={{overflowY: 'auto'}}>
      <SidebarSection title="Definition">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <SidebarTitle>{assetKeyToString(node.assetKey)}</SidebarTitle>
          <Description description={node.description || null} />
        </Box>
        {definition.metadata && Plugin && Plugin.SidebarComponent && (
          <Plugin.SidebarComponent definition={definition} repoAddress={repoAddress} />
        )}
      </SidebarSection>

      <div style={{borderBottom: `2px solid ${ColorsWIP.Gray300}`}} />
      <SidebarSection title={'Materialization in Last Run'}>
        {node.assetMaterializations.length ? (
          <>
            <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
              <LatestMaterializationMetadata latest={node.assetMaterializations[0]} asOf={null} />
            </div>
            <Box margin={{bottom: 12, horizontal: 12, top: 8}}>
              <AssetCatalogLink to={`/instance/assets/${node.assetKey.path.join('/')}`}>
                {'View All in Asset Catalog '}
                <IconWIP name="open_in_new" color={ColorsWIP.Blue500} />
              </AssetCatalogLink>
            </Box>
          </>
        ) : (
          <Box margin={12}>&mdash;</Box>
        )}
      </SidebarSection>

      {node.assetMaterializations.length ? (
        <SidebarSection title={'Materialization Plots'}>
          <AssetMaterializations assetKey={node.assetKey} asSidebarSection />
        </SidebarSection>
      ) : null}
    </div>
  );
};

const AssetCatalogLink = styled(Link)`
  display: flex;
  gap: 5px;
  align-items: center;
  justify-content: flex-end;
  margin-top: -10px;
`;
