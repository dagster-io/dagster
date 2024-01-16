import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {AssetLiveDataThreadManager} from '../../asset-data/AssetLiveDataThreadManager';
import {AssetNode} from '../AssetNode';
import {tokenForAssetKey} from '../Utils';
import {
  AssetNodeScenariosBase,
  AssetNodeScenariosPartitioned,
  AssetNodeScenariosSource,
} from '../__fixtures__/AssetNode.fixtures';

const Scenarios = [
  ...AssetNodeScenariosBase,
  ...AssetNodeScenariosPartitioned,
  ...AssetNodeScenariosSource,
];

describe('AssetNode', () => {
  Scenarios.forEach((scenario) =>
    it(`renders ${scenario.expectedText.join(',')} when ${scenario.title}`, async () => {
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

      function SetCacheEntry() {
        AssetLiveDataThreadManager.__setCacheEntryForTest(
          tokenForAssetKey(definitionCopy.assetKey),
          scenario.liveData,
        );
        return null;
      }

      render(
        <MemoryRouter>
          <MockedProvider>
            <AssetLiveDataProvider>
              <SetCacheEntry />
              <AssetNode definition={definitionCopy} selected={false} />
            </AssetLiveDataProvider>
          </MockedProvider>
        </MemoryRouter>,
      );

      await waitFor(() => {
        const assetKey = definitionCopy.assetKey;
        const displayName = assetKey.path[assetKey.path.length - 1]!;
        expect(screen.getByText(displayName)).toBeVisible();
        for (const text of scenario.expectedText) {
          expect(screen.getByText(new RegExp(text))).toBeVisible();
        }
      });
    }),
  );
});
