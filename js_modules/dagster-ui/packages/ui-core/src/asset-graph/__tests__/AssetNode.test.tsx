import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';

import {_setCacheEntryForTest} from '../../asset-data/AssetLiveDataProvider';
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
      _setCacheEntryForTest(definitionCopy.assetKey, scenario.liveData);

      render(
        <MemoryRouter>
          <AssetNode definition={definitionCopy} selected={false} />
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
