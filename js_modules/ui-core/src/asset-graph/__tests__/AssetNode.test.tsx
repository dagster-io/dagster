import {MockedProvider} from '@apollo/client/testing';
import {Colors} from '@dagster-io/ui-components';
import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import * as Flags from '../../app/Flags';
import {withMiddleTruncation} from '../../app/Util';
import {AssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {AssetHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {AssetStaleStatusData} from '../../asset-data/AssetStaleStatusDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {
  buildAssetKey,
  buildAssetNode,
  buildDefinitionTag,
  buildStaleCause,
} from '../../graphql/builders';
import {AssetNameRow, AssetNode} from '../AssetNode';
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

jest.mock('@shared/app/assetHealthEnabled', () => ({
  assetHealthEnabled: jest.fn(() => true),
}));

/** The tests in this file mirror the stories in the storybook. If you've made
 * changes to the AssetNode rendering, consider opening the storybook and updating
 * the `expectedText` for each scenario to match what is rendered. Then these tests
 * should all pass.
 * */
describe('AssetNode', function () {
  afterAll(() => {
    jest.unmock('@shared/app/assetHealthEnabled');
  });

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
              staleCauses: staleCauses.map((cause: any) => buildStaleCause(cause)),
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

describe('AssetNameRow', () => {
  it('uses the custom header background for the truncated-name tooltip style', () => {
    const displayName = 'very_long_asset_name_that_should_truncate_in_the_asset_graph';
    const definition = buildAssetNode({
      assetKey: buildAssetKey({path: [displayName]}),
      isMaterializable: true,
      tags: [buildDefinitionTag({key: 'dagster/ui_color', value: 'blue'})],
    });

    render(
      <AssetNameRow definition={definition} $customBackground={Colors.backgroundBlueHover()} />,
    );

    const tooltipTarget = screen.getByText(
      withMiddleTruncation(displayName, {
        maxLength: ASSET_NODE_NAME_MAX_LENGTH,
      }),
    );

    expect(JSON.parse(tooltipTarget.getAttribute('data-tooltip-style') || '{}')).toMatchObject({
      background: Colors.backgroundBlueHover(),
    });
  });
});

function scenarioAssetKey(scenario: AssetNodeScenario) {
  return buildAssetKey({
    path: scenario.liveData ? [scenario.liveData.stepKey] : JSON.parse(scenario.definition.id),
  });
}
