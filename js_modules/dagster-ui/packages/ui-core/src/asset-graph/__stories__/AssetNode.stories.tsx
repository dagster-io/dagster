import {MockedProvider} from '@apollo/client/testing';
import {Box, Checkbox} from '@dagster-io/ui-components';
import {useState} from 'react';

import {AssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {AssetHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {AssetStaleStatusData} from '../../asset-data/AssetStaleStatusDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {KNOWN_TAGS} from '../../graph/OpTags';
import {
  AssetKey,
  StaleCause,
  buildAssetKey,
  buildAssetNode,
  buildStaleCause,
} from '../../graphql/types';
import {
  AssetNode,
  AssetNodeMinimalWithHealth,
  AssetNodeMinimalWithoutHealth,
  AssetNodeWithLiveData,
} from '../AssetNode';
import {AllAssetNodeFacets} from '../AssetNodeFacets';
import {AssetNodeFacetsPicker} from '../AssetNodeFacetsPicker';
import {AssetNodeFacet} from '../AssetNodeFacetsUtil';
import {AssetNodeLink} from '../ForeignNode';
import {tokenForAssetKey} from '../Utils';
import * as Mocks from '../__fixtures__/AssetNode.fixtures';
import {getAssetNodeDimensions} from '../layout';

// eslint-disable-next-line import/no-default-export
export default {
  title: 'Asset Graph/AssetNode',
  component: AssetNode,
};

interface AssetNodeScenario {
  title: string;
  liveData: any;
  healthData?: AssetHealthFragment;
  definition: any;
  expectedText: string[];
}

function SetCacheEntry({
  assetKey,
  liveData,
  healthData,
}: {
  assetKey: AssetKey;
  liveData: any;
  healthData?: AssetHealthFragment;
}) {
  const key = tokenForAssetKey(assetKey);

  // // Set up live data cache if available
  if (liveData) {
    const entry = {[key]: liveData};
    AssetBaseData.manager._updateCache(entry);

    const staleEntry = {
      [key]: buildAssetNode({
        assetKey,
        staleCauses: liveData.staleCauses.map((cause: StaleCause) => buildStaleCause(cause)),
        staleStatus: liveData.staleStatus,
      }),
    };
    AssetStaleStatusData.manager._updateCache(staleEntry);
  }
  if (healthData) {
    const healthEntry = {[key]: {...healthData, key: assetKey}};
    AssetHealthData.manager._updateCache(healthEntry);
  }
  return null;
}

export const LiveStates = () => {
  const [hasAssetHealth, setHasAssetHealth] = useState(true);
  const [facets, setFacets] = useState<Set<AssetNodeFacet>>(new Set(AllAssetNodeFacets));

  const caseWithLiveData = (scenario: AssetNodeScenario) => {
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

    const dimensions = getAssetNodeDimensions(facets);

    return (
      <>
        <SetCacheEntry
          healthData={scenario.healthData}
          liveData={scenario.liveData}
          assetKey={definitionCopy.assetKey}
        />
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
            <AssetNodeWithLiveData
              liveData={scenario.liveData}
              definition={definitionCopy}
              selected={false}
              facets={facets}
              hasAssetHealth={hasAssetHealth}
            />
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
              {hasAssetHealth ? (
                <AssetNodeMinimalWithHealth
                  definition={definitionCopy}
                  selected={false}
                  height={82}
                  facets={facets}
                />
              ) : (
                <AssetNodeMinimalWithoutHealth
                  definition={definitionCopy}
                  selected={false}
                  height={82}
                  facets={facets}
                />
              )}
            </div>
          </div>
        </Box>
      </>
    );
  };

  return (
    <MockedProvider>
      <AssetLiveDataProvider>
        <Checkbox
          checked={hasAssetHealth}
          label="Asset Health Available (Cloud)"
          onChange={() => setHasAssetHealth(!hasAssetHealth)}
        />

        <AssetNodeFacetsPicker value={facets} onChange={setFacets} />
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

    const facets = new Set(AllAssetNodeFacets);
    const dimensions = getAssetNodeDimensions(facets);
    const assetKey = buildAssetKey({path: [liveData.stepKey]});

    return (
      <>
        <SetCacheEntry liveData={liveData} assetKey={assetKey} />
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
            <AssetNodeWithLiveData
              liveData={liveData}
              facets={facets}
              definition={def}
              selected={false}
              hasAssetHealth
            />
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
