import {MockedProvider} from '@apollo/client/testing';
import {Box} from '@dagster-io/ui-components';

import {AssetLiveDataProvider, factory} from '../../asset-data/AssetLiveDataProvider';
import {KNOWN_TAGS} from '../../graph/OpTags';
import {buildAssetKey} from '../../graphql/types';
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
        path: [],
      },
    };
    definitionCopy.assetKey.path = scenario.liveData
      ? [scenario.liveData.stepKey]
      : JSON.parse(scenario.definition.id);

    const dimensions = getAssetNodeDimensions(definitionCopy);

    function SetCacheEntry() {
      factory.manager._updateCache({
        [tokenForAssetKey(definitionCopy.assetKey)]: scenario.liveData!,
      });
      return null;
    }

    return (
      <>
        <SetCacheEntry />
        <Box flex={{direction: 'column', gap: 8, alignItems: 'flex-start'}}>
          <div
            style={{
              position: 'relative',
              width: dimensions.width,
              height: dimensions.height,
              overflowY: 'hidden',
            }}
          >
            <AssetNode definition={definitionCopy} selected={false} />
          </div>
          <div style={{position: 'relative', width: dimensions.width, height: 104}}>
            <div style={{position: 'absolute', width: dimensions.width}}>
              <AssetNodeMinimal definition={definitionCopy} selected={false} height={82} />
            </div>
          </div>
          <code>
            <strong>{scenario.title}</strong>
          </code>
        </Box>
      </>
    );
  };

  return (
    <MockedProvider>
      <AssetLiveDataProvider>
        <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
          {Mocks.AssetNodeScenariosBase.map(caseWithLiveData)}
        </Box>

        <Box flex={{gap: 20, wrap: 'wrap', alignItems: 'flex-start'}}>
          {Mocks.AssetNodeScenariosSource.map(caseWithLiveData)}
        </Box>
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
    const def = {...Mocks.AssetNodeFragmentBasic, computeKind};
    const liveData = Mocks.LiveDataForNodeMaterialized;

    function SetCacheEntry() {
      factory.manager._updateCache({
        [tokenForAssetKey(buildAssetKey({path: [liveData.stepKey]}))]: liveData!,
      });
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
