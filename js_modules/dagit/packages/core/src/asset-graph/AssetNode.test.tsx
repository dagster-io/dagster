import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

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
        <MemoryRouter>
          <AssetNode
            definition={scenario.definition}
            liveData={scenario.liveData}
            selected={false}
          />
        </MemoryRouter>,
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
