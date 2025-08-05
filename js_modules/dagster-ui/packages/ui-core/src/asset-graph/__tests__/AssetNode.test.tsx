import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import * as Flags from '../../app/Flags';
import {withMiddleTruncation} from '../../app/Util';
import {AssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {AssetStaleStatusData} from '../../asset-data/AssetStaleStatusDataProvider';
import {buildAssetNode, buildStaleCause} from '../../graphql/types';
import {AssetNode} from '../AssetNode';
import {tokenForAssetKey} from '../Utils';
import {
  AssetNodeScenariosBase,
  AssetNodeScenariosPartitioned,
  AssetNodeScenariosSource,
} from '../__fixtures__/AssetNode.fixtures';
import {ASSET_NODE_NAME_MAX_LENGTH} from '../layout';

const Scenarios = [
  ...AssetNodeScenariosBase,
  ...AssetNodeScenariosPartitioned,
  ...AssetNodeScenariosSource,
];

describe('AssetNode', () => {
  Scenarios.forEach((scenario) =>
    it(`renders ${scenario.expectedText.join(',')} when ${scenario.title}`, async () => {
      jest.spyOn(Flags, 'featureEnabled').mockImplementation((flag) => {
        return flag === FeatureFlag.flagUseNewObserveUIs ? false : true;
      });

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
        if (scenario.liveData) {
          const key = tokenForAssetKey(definitionCopy.assetKey);
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          const entry = {[key]: scenario.liveData!};
          // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
          const {staleStatus, staleCauses} = scenario.liveData!;
          const staleEntry = {
            [key]: buildAssetNode({
              assetKey: definitionCopy.assetKey,
              staleCauses: staleCauses.map((cause) => buildStaleCause(cause)),
              staleStatus,
            }),
          };
          AssetStaleStatusData.manager._updateCache(staleEntry);
          AssetBaseData.manager._updateCache(entry);
        }
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
