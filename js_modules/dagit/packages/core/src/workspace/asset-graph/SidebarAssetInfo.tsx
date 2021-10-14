import React from 'react';
import {Link} from 'react-router-dom';
import styled from 'styled-components/macro';

import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {LatestMaterializationMetadata} from '../../assets/LastMaterializationMetadata';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {PipelineExplorerSolidHandleFragment} from '../../pipelines/types/PipelineExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {Box} from '../../ui/Box';
import {ColorsWIP} from '../../ui/Colors';
import {IconWIP} from '../../ui/Icon';
import {RepoAddress} from '../types';

import {assetKeyToString} from './Utils';
import {AssetGraphQuery_repositoryOrError_Repository_assetNodes} from './types/AssetGraphQuery';

export const SidebarAssetInfo: React.FC<{
  node: AssetGraphQuery_repositoryOrError_Repository_assetNodes;
  handle: PipelineExplorerSolidHandleFragment;
  repoAddress: RepoAddress;
}> = ({node, handle, repoAddress}) => {
  const definition = handle.solid.definition;
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
          <Box margin={12}>
            <AssetCatalogLink to={`/instance/assets/${node.assetKey.path.join('/')}`}>
              {'View All in Asset Catalog '}
              <IconWIP name="open_in_new" color={ColorsWIP.Blue500} />
            </AssetCatalogLink>
            <LatestMaterializationMetadata latest={node.assetMaterializations[0]} asOf={null} />
          </Box>
        ) : (
          <Box margin={12}>&mdash;</Box>
        )}
      </SidebarSection>

      {node.assetMaterializations.length ? (
        <SidebarSection title={'Materialization Plots'}>
          <Box margin={12}>
            <AssetMaterializations assetKey={node.assetKey} asOf={null} asSidebarSection />
          </Box>
        </SidebarSection>
      ) : null}
    </div>
  );
};

const AssetCatalogLink = styled(Link)`
  position: absolute;
  top: 5px;
  right: 10px;
  display: flex;
  gap: 5px;
  align-items: center;
`;
