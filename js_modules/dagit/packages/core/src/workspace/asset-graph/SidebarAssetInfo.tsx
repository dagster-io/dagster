import {Colors, Icon} from '@blueprintjs/core';
import React from 'react';
import {Link} from 'react-router-dom';

import {AssetDetails} from '../../assets/AssetDetails';
import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {PipelineExplorerSolidHandleFragment} from '../../pipelines/types/PipelineExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {Box} from '../../ui/Box';
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
      <SidebarSection title="Static Definition">
        <Box margin={12}>
          <SidebarTitle>{assetKeyToString(node.assetKey)}</SidebarTitle>
          <Description description={node.description || null} />
        </Box>
        {definition.metadata && Plugin && Plugin.SidebarComponent && (
          <Plugin.SidebarComponent definition={definition} repoAddress={repoAddress} />
        )}
      </SidebarSection>

      <div style={{borderBottom: `2px solid ${Colors.GRAY5}`}} />
      <SidebarSection title={'Materialization in Last Run'}>
        {node.assetMaterializations.length ? (
          <Box margin={12}>
            <Link
              to={`/instance/assets/${node.assetKey.path.join('/')}`}
              style={{
                position: 'absolute',
                top: 20,
                right: 10,
                display: 'flex',
                gap: 5,
                alignItems: 'center',
              }}
            >
              {'View All in Asset Catalog '}
              <IconWIP name="open_in_new" size={16} color={Colors.BLUE3} />
            </Link>
            <AssetDetails assetKey={node.assetKey} asOf={null} asSidebarSection />
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
