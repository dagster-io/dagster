import {render, screen, waitFor} from '@testing-library/react';
import * as React from 'react';
import {MemoryRouter} from 'react-router-dom';

import {AssetNode} from '../AssetNode';
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
        const assetKey = scenario.definition.assetKey;
        const displayName = assetKey.path[assetKey.path.length - 1];
        expect(screen.getByText(displayName)).toBeVisible();
        for (const text of scenario.expectedText) {
          expect(screen.getByText(new RegExp(text))).toBeVisible();
        }
      });
    }),
  );
});
