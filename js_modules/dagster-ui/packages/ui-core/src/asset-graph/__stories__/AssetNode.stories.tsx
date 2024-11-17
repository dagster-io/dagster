import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';
import React from 'react';

import {AssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {AssetStaleStatusData} from '../../asset-data/AssetStaleStatusDataProvider';
import {KNOWN_TAGS} from '../../graph/OpTags';
import {buildAssetKey, buildAssetNode, buildStaleCause} from '../../graphql/types';
import {AssetNode, AssetNodeMinimal} from '../AssetNode';
import {AssetNodeLink} from '../ForeignNode';
import {tokenForAssetKey} from '../Utils';
import * as Mocks from '../__fixtures__/AssetNode.fixtures';
import {getAssetNodeDimensions} from '../layout';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Graph/AssetNode',
  component: AssetNode,
};

export const LiveStates = () => {
  const caseWithLiveData = (scenario: (typeof Mocks.AssetNodeScenariosBase)[0]) => {
    const definitionCopy = {
      ...scenario.definition,
      assetKey: {
        ...scenario.definition.assetKey,
        path: [] as string[],
      },
    };
    definitionCopy.assetKey.path = scenario.liveData
      ? [scenario.liveData.stepKey]
      : JSON.parse(scenario.definition.id);

    const dimensions = getAssetNodeDimensions(definitionCopy);

    function SetCacheEntry() {
      if (!scenario.liveData) {
        return null;
      }
      const entry = {[tokenForAssetKey(definitionCopy.assetKey)]: scenario.liveData};
      const {staleStatus, staleCauses} = scenario.liveData;
      const staleEntry = {
        [tokenForAssetKey(definitionCopy.assetKey)]: buildAssetNode({
          assetKey: definitionCopy.assetKey,
          staleCauses: staleCauses.map((cause) => buildStaleCause(cause)),
          staleStatus,
        }),
      };
      AssetStaleStatusData.manager._updateCache(staleEntry);
      AssetBaseData.manager._updateCache(entry);
      return null;
    }

    return (
      <>
        <SetCacheEntry />
        <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
          <code style={{marginTop: 20}}>
            <strong>{scenario.title}</strong>
          </code>
          <div
            style={{
              position: 'relative',
              width: dimensions.width,
              height: dimensions.height,
              background: `linear-gradient(to bottom, rgba(100,100,100,0.15) 49%, rgba(100,100,100,1) 50%, rgba(100,100,100,0.15) 51%)`,
              overflowY: 'hidden',
            }}
          >
            <AssetNode definition={definitionCopy} selected={false} />
          </div>
          <div
            style={{
              position: 'relative',
              width: dimensions.width,
              background: `rgba(100,100,100,0.15)`,
              height: 90,
            }}
          >
            <div style={{position: 'absolute', width: dimensions.width, transform: 'scale(0.4)'}}>
              <AssetNodeMinimal definition={definitionCopy} selected={false} height={82} />
            </div>
          </div>
        </Box>
      </>
    );
  };

  return (
    <MockedProvider>
      <AssetLiveDataProvider>
        <h2>Base Assets</h2>
        <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
          {Mocks.AssetNodeScenariosBase.map(caseWithLiveData)}
        </Box>
        <h2>Source Assets</h2>
        <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
          {Mocks.AssetNodeScenariosSource.map(caseWithLiveData)}
        </Box>
        <h2>Partitioned Assets</h2>
        <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
          {Mocks.AssetNodeScenariosPartitioned.map(caseWithLiveData)}
        </Box>
      </AssetLiveDataProvider>
    </MockedProvider>
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
    const def = {...Mocks.AssetNodeFragmentBasic, kinds: [computeKind]};
    const liveData = Mocks.LiveDataForNodeMaterialized;

    function SetCacheEntry() {
      const assetKey = buildAssetKey({path: [liveData.stepKey]});
      const key = tokenForAssetKey(assetKey);
      const entry = {[key]: liveData!};
      const {staleStatus, staleCauses} = liveData!;
      const staleEntry = {
        [key]: buildAssetNode({
          assetKey,
          staleCauses: staleCauses.map((cause) => buildStaleCause(cause)),
          staleStatus,
        }),
      };
      AssetStaleStatusData.manager._updateCache(staleEntry);
      AssetBaseData.manager._updateCache(entry);
      return null;
    }

    const dimensions = getAssetNodeDimensions(def);

    return (
      <>
        <SetCacheEntry />
        <Box flex={{direction: 'column', gap: 0, alignItems: 'flex-start'}}>
          <strong>{computeKind}</strong>
          <div
            style={{
              position: 'relative',
              width: 280,
              height: dimensions.height,
              overflowY: 'hidden',
              background: `linear-gradient(to bottom, transparent 49%, gray 50%, transparent 51%)`,
            }}
          >
            <AssetNode definition={def} selected={false} />
          </div>
        </Box>
      </>
    );
  };

  return (
    <MockedProvider>
      <AssetLiveDataProvider>
        <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
          {Object.keys(KNOWN_TAGS).map(caseWithComputeKind)}
          {caseWithComputeKind('Unknown-Kind-Long')}
          {caseWithComputeKind('another')}
        </Box>
      </AssetLiveDataProvider>
    </MockedProvider>
  );
};
