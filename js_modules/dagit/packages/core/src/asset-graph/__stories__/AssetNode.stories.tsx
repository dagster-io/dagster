import {Box} from '@dagster-io/ui';
import React from 'react';

import {KNOWN_TAGS} from '../../graph/OpTags';
import {AssetNode, AssetNodeMinimal} from '../AssetNode';
import {AssetNodeLink} from '../ForeignNode';
import * as Mocks from '../__fixtures__/AssetNode.fixtures';
import {getAssetNodeDimensions} from '../layout';

// eslint-disable-next-line import/no-default-export
export default {component: AssetNode};

export const LiveStates = () => {
  const caseWithLiveData = (scenario: typeof Mocks.AssetNodeScenariosBase[0]) => {
    const dimensions = getAssetNodeDimensions(scenario.definition);
    return (
      <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
        <div
          style={{
            position: 'relative',
            width: dimensions.width,
            height: dimensions.height,
            overflowY: 'hidden',
          }}
        >
          <AssetNode
            definition={scenario.definition}
            liveData={scenario.liveData}
            selected={false}
          />
        </div>
        <div style={{position: 'relative', width: dimensions.width, height: 82}}>
          <div style={{position: 'absolute', width: dimensions.width, height: 82}}>
            <AssetNodeMinimal
              definition={scenario.definition}
              liveData={scenario.liveData}
              selected={false}
            />
          </div>
        </div>
        <code>
          <strong>{scenario.title}</strong>
          <pre>{JSON.stringify(scenario.liveData, null, 2)}</pre>
        </code>
      </Box>
    );
  };

  return (
    <>
      <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
        {Mocks.AssetNodeScenariosBase.map(caseWithLiveData)}
      </Box>

      <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
        {Mocks.AssetNodeScenariosSource.map(caseWithLiveData)}
      </Box>
      <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
        {Mocks.AssetNodeScenariosPartitioned.map(caseWithLiveData)}
      </Box>
    </>
  );
  return;
};

export const Links = () => {
  return (
    <Box flex={{direction: 'column', gap: 0, alignItems: 'flex-start'}}>
      <AssetNodeLink assetKey={{path: ['short_name']}} />
      <AssetNodeLink assetKey={{path: ['multicomponent', 'key', 'path']}} />
      <AssetNodeLink assetKey={{path: ['very_long_asset_in_another_graph']}} />
    </Box>
  );
};
export const PartnerTags = () => {
  const caseWithComputeKind = (computeKind: string) => {
    const def = {...Mocks.AssetNodeFragmentBasic, computeKind};
    const liveData = Mocks.LiveDataForNodeMaterialized;
    const dimensions = getAssetNodeDimensions(def);

    return (
      <Box flex={{direction: 'column', gap: 0, alignItems: 'flex-start'}}>
        <strong>{computeKind}</strong>
        <div
          style={{position: 'relative', width: 280, height: dimensions.height, overflowY: 'hidden'}}
        >
          <AssetNode definition={def} selected={false} liveData={liveData} />
        </div>
      </Box>
    );
  };

  return (
    <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
      {Object.keys(KNOWN_TAGS).map(caseWithComputeKind)}
      {caseWithComputeKind('Unknown-Kind-Long')}
      {caseWithComputeKind('another')}
    </Box>
  );
};
