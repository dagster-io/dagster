import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';

import {TestProvider} from '../testing/TestProvider';

import {AssetNode} from './AssetNode';
import {
  AssetNodeScenariosBase,
  AssetNodeScenariosPartitioned,
  AssetNodeScenariosSource,
} from './AssetNode.mocks';
import {displayNameForAssetKey} from './Utils';

const Scenarios = [
  ...AssetNodeScenariosBase,
  ...AssetNodeScenariosPartitioned,
  ...AssetNodeScenariosSource,
];

describe('AssetNode', () => {
  Scenarios.forEach((scenario) =>
    it(`renders ${scenario.expectedText.join(',')} when ${scenario.title}`, async () => {
      render(
        <TestProvider>
          <AssetNode
            definition={scenario.definition}
            liveData={scenario.liveData}
            selected={false}
          />
        </TestProvider>,
      );

      await waitFor(() => {
        const displayName = displayNameForAssetKey(scenario.definition.assetKey);
        expect(screen.getByText(displayName)).toBeVisible();
        for (const text of scenario.expectedText) {
          expect(screen.getByText(new RegExp(text))).toBeVisible();
        }
      });
    }),
  );
});
