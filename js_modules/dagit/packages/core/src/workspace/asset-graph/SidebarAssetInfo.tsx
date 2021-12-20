import React from 'react';

import {displayNameForAssetKey} from '../../app/Util';
import {AssetMaterializations} from '../../assets/AssetMaterializations';
import {Description} from '../../pipelines/Description';
import {SidebarSection, SidebarTitle} from '../../pipelines/SidebarComponents';
import {GraphExplorerSolidHandleFragment_solid_definition} from '../../pipelines/types/GraphExplorerSolidHandleFragment';
import {pluginForMetadata} from '../../plugins';
import {Box} from '../../ui/Box';
import {ColorsWIP} from '../../ui/Colors';
import {RepoAddress} from '../types';

import {LaunchAssetExecutionButton} from './LaunchAssetExecutionButton';
import {LiveDataForNode} from './Utils';
import {AssetGraphQuery_pipelineOrError_Pipeline_assetNodes} from './types/AssetGraphQuery';

export const SidebarAssetInfo: React.FC<{
  definition: GraphExplorerSolidHandleFragment_solid_definition;
  node: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes;
  liveData: LiveDataForNode;
  repoAddress: RepoAddress;
}> = ({node, definition, repoAddress, liveData}) => {
  const Plugin = pluginForMetadata(definition.metadata);
  const {lastMaterialization} = liveData || {};

  return (
    <>
      <SidebarSection title="Definition">
        <Box padding={{vertical: 16, horizontal: 24}}>
          <Box
            flex={{gap: 8, justifyContent: 'space-between', alignItems: 'baseline'}}
            margin={{bottom: 8}}
          >
            <SidebarTitle>{displayNameForAssetKey(node.assetKey)}</SidebarTitle>
            <LaunchAssetExecutionButton assets={[node]} repoAddress={repoAddress} />
          </Box>
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
        liveData={liveData}
        paramsTimeWindowOnly={false}
        params={{}}
        setParams={() => {}}
      />
    </>
  );
};

export const SidebarAssetsInfo: React.FC<{
  nodes: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes[];
  repoAddress: RepoAddress;
}> = ({nodes, repoAddress}) => {
  return (
    <SidebarSection title="Definition">
      <Box padding={{vertical: 16, horizontal: 24}}>
        <Box
          flex={{gap: 8, justifyContent: 'space-between', alignItems: 'baseline'}}
          margin={{bottom: 8}}
        >
          <SidebarTitle>{`${nodes.length} Assets Selected`}</SidebarTitle>
          <LaunchAssetExecutionButton repoAddress={repoAddress} assets={nodes} />
        </Box>
      </Box>
    </SidebarSection>
  );
};
