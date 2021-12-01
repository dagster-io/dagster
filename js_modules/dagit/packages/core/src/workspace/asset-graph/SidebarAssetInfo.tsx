import React from 'react';

import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {Box} from '../../ui/Box';
import {ColorsWIP} from '../../ui/Colors';
import {RepoAddress} from '../types';

import {assetKeyToString, LiveDataForNode} from './Utils';
import {AssetGraphQuery_pipelineOrError_Pipeline_assetNodes} from './types/AssetGraphQuery';

export const SidebarAssetInfo: React.FC<{
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes;
  liveData: LiveDataForNode;
  repoAddress: RepoAddress;
}> = ({node, definition, repoAddress, liveData}) => {
  const Plugin = pluginForMetadata(definition.metadata);
  const {inProgressRunIds, lastMaterialization} = liveData || {};

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

      <AssetMaterializations
        assetKey={node.assetKey}
        assetLastMaterializedAt={lastMaterialization?.materializationEvent.timestamp}
        asSidebarSection
        inProgressRunIds={inProgressRunIds}
        paramsTimeWindowOnly={false}
        params={{}}
        setParams={() => {}}
      />
    </div>
  );
};
