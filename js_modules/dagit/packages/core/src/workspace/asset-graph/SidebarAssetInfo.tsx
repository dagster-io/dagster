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

import {InProgressRunsBanner} from './InProgressRunsBanner';
import {assetKeyToString, LiveDataForNode} from './Utils';
import {AssetGraphQuery_pipelineOrError_Pipeline_assetNodes} from './types/AssetGraphQuery';

export const SidebarAssetInfo: React.FC<{
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes;
  liveData: LiveDataForNode;
  repoAddress: RepoAddress;
}> = ({node, definition, repoAddress, liveData}) => {
  const Plugin = pluginForMetadata(definition.metadata);
  const {lastMaterialization, inProgressRunIds} = liveData || {};

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
      <InProgressRunsBanner runIds={inProgressRunIds || []} />

      <SidebarSection title={'Materialization in Last Run'}>
        {lastMaterialization ? (
          <>
            <div style={{margin: -1, maxWidth: '100%', overflowX: 'auto'}}>
              <LatestMaterializationMetadata latest={lastMaterialization} asOf={null} />
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

      {lastMaterialization ? (
        <SidebarSection title={'Materialization Plots'}>
          <AssetMaterializations
            assetKey={node.assetKey}
            asSidebarSection
            paramsTimeWindowOnly={false}
            params={{}}
            setParams={() => {}}
          />
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
