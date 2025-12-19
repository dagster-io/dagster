import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import * as Flags from '../../app/Flags';
import {withMiddleTruncation} from '../../app/Util';
import {AssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {AssetHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {AssetStaleStatusData} from '../../asset-data/AssetStaleStatusDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {StaleCause, buildAssetKey, buildAssetNode, buildStaleCause} from '../../graphql/types';
import {AssetNode} from '../AssetNode';
import {AllAssetNodeFacets} from '../AssetNodeFacets';
import {tokenForAssetKey} from '../Utils';
import {
  AssetNodeScenariosBase,
  AssetNodeScenariosPartitioned,
  AssetNodeScenariosSource,
} from '../__fixtures__/AssetNode.fixtures';
import {ASSET_NODE_NAME_MAX_LENGTH} from '../layout';

interface AssetNodeScenario {
  title: string;
  liveData: any;
  healthData?: AssetHealthFragment;
  definition: any;
  expectedText: string[];
}

const Scenarios = [
  ...AssetNodeScenariosBase,
  ...AssetNodeScenariosPartitioned,
  ...AssetNodeScenariosSource,
];

const mockAllAssetKeys = new Set(Scenarios.map((s) => tokenForAssetKey(scenarioAssetKey(s))));
jest.mock('../../assets/useAllAssets', () => ({
  useAllAssetsNodes: () => ({allAssetKeys: mockAllAssetKeys, loading: false}),
}));

/** The tests in this file mirror the stories in the storybook. If you've made
 * changes to the AssetNode rendering, consider opening the storybook and updating
 * the `expectedText` for each scenario to match what is rendered. Then these tests
 * should all pass.
 * */
describe('AssetNode', function () {
  beforeEach(function () {});

  Scenarios.forEach((scenario: AssetNodeScenario) =>
    it(`renders ${scenario.expectedText.join(',')} when ${scenario.title}`, async () => {
      jest.spyOn(Flags, 'featureEnabled').mockImplementation(() => true);

      const definitionCopy = {
        ...scenario.definition,
        assetKey: scenarioAssetKey(scenario),
      };

      function SetCacheEntry() {
        const key = tokenForAssetKey(definitionCopy.assetKey);

        if (scenario.liveData) {
          const entry = {[key]: scenario.liveData};
          const {staleStatus, staleCauses} = scenario.liveData;
          const staleEntry = {
            [key]: buildAssetNode({
              assetKey: definitionCopy.assetKey,
              staleCauses: staleCauses.map((cause: StaleCause) => buildStaleCause(cause)),
              staleStatus,
            }),
          };
          AssetStaleStatusData.manager._updateCache(staleEntry);
          AssetBaseData.manager._updateCache(entry);
        }

        if (scenario.healthData) {
          const healthEntry = {
            [key]: {
              ...scenario.healthData,
              key: definitionCopy.assetKey,
            },
          };
          AssetHealthData.manager._updateCache(healthEntry);
        }
        return null;
      }

      render(
        <MemoryRouter>
          <MockedProvider>
            <AssetLiveDataProvider>
              <SetCacheEntry />
              <AssetNode
                facets={new Set(AllAssetNodeFacets)}
                definition={definitionCopy}
                selected={false}
              />
            </AssetLiveDataProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      await waitFor(() => {
        const assetKey = definitionCopy.assetKey;
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const displayName = assetKey.path[assetKey.path.length - 1]!;
        expect(
          screen.getByText(
            withMiddleTruncation(displayName, {
              maxLength: ASSET_NODE_NAME_MAX_LENGTH,
            }),
          ),
        ).toBeVisible();
        for (const text of scenario.expectedText) {
          expect(screen.getByText(new RegExp(text))).toBeVisible();
        }
      });
    }),
  );
});

function scenarioAssetKey(scenario: AssetNodeScenario) {
  return buildAssetKey({
    path: scenario.liveData ? [scenario.liveData.stepKey] : JSON.parse(scenario.definition.id),
  });
}
