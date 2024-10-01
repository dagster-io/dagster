import {MockedProvider} from '@apollo/client/testing';
import {act, render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router-dom';
import {RecoilRoot} from 'recoil';

import {ASSETS_GRAPH_LIVE_QUERY} from '../../asset-data/AssetBaseDataProvider';
import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {
  AssetGraphLiveQuery,
  AssetGraphLiveQueryVariables,
} from '../../asset-data/types/AssetBaseDataProvider.types';
import {
  AssetGraphQuery,
  AssetGraphQueryVariables,
} from '../../asset-graph/types/useAssetGraphData.types';
import {ASSET_GRAPH_QUERY} from '../../asset-graph/useAssetGraphData';
import {
  AssetKeyInput,
  buildAssetKey,
  buildAssetLatestInfo,
  buildAssetNode,
} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {AssetView} from '../AssetView';
import {
  AssetViewDefinitionNonSDA,
  AssetViewDefinitionSDA,
  AssetViewDefinitionSourceAsset,
  LatestMaterializationTimestamp,
  RootWorkspaceWithOneLocation,
} from '../__fixtures__/AssetViewDefinition.fixtures';

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

// These files must be mocked because useVirtualizer tries to create a ResizeObserver,
// and the component tree fails to mount.
jest.mock('../AssetPartitions', () => ({AssetPartitions: () => <div />}));
jest.mock('../AssetEvents', () => ({AssetEvents: () => <div />}));

function mockLiveData(key: string) {
  const assetKey = {path: [key]};
  return buildQueryMock<AssetGraphLiveQuery, AssetGraphLiveQueryVariables>({
    query: ASSETS_GRAPH_LIVE_QUERY,
    variables: {
      assetKeys: [assetKey],
    },
    data: {
      assetNodes: [buildAssetNode({assetKey: buildAssetKey(assetKey)})],
      assetsLatestInfo: [buildAssetLatestInfo({assetKey: buildAssetKey(assetKey)})],
    },
  });
}

describe('AssetView', () => {
  const Test = ({path, assetKey}: {path: string; assetKey: AssetKeyInput}) => {
    return (
      <RecoilRoot>
        <MockedProvider
          mocks={[
            ...RootWorkspaceWithOneLocation,
            AssetViewDefinitionSDA,
            AssetViewDefinitionNonSDA,
            AssetViewDefinitionSourceAsset,
            mockLiveData('sda_asset'),
            mockLiveData('observable_source_asset'),
            mockLiveData('non_sda_asset'),
            buildQueryMock<AssetGraphQuery, AssetGraphQueryVariables>({
              query: ASSET_GRAPH_QUERY,
              variables: {},
              data: {
                assetNodes: [buildAssetNode()],
              },
            }),
          ]}
        >
          <WorkspaceProvider>
            <AssetLiveDataProvider>
              <MemoryRouter initialEntries={[path]}>
                <AssetView assetKey={assetKey} headerBreadcrumbs={[]} currentPath={assetKey.path} />
              </MemoryRouter>
            </AssetLiveDataProvider>
          </WorkspaceProvider>
        </MockedProvider>
      </RecoilRoot>
    );
  };

  const MESSAGE = /this is a historical view of materializations as of \./i;

  describe('Launch button', () => {
    it('shows the "Materialize" button for a software-defined asset', async () => {
      render(<Test path="/sda_asset" assetKey={{path: ['sda_asset']}} />);
      expect(await screen.findByText('Materialize')).toBeVisible();
    });

    it('shows the "Observe" button for a software-defined source asset', async () => {
      render(
        <Test path="/observable_source_asset" assetKey={{path: ['observable_source_asset']}} />,
      );
      expect(await screen.findByText('Observe')).toBeVisible();
    });

    it('shows no button for a non-software defined asset', async () => {
      render(<Test path="/non_sda_asset" assetKey={{path: ['non_sda_asset']}} />);
      expect(screen.queryByText('Observe')).toBeNull();
      expect(screen.queryByText('Materialize')).toBeNull();
    });
  });

  describe('Historical view alert', () => {
    it('shows historical view alert if `asOf` is old', async () => {
      render(<Test path="/non_sda_asset?asOf=10" assetKey={{path: ['non_sda_asset']}} />);
      expect(await screen.findByText(MESSAGE)).toBeVisible();
    });

    // Test is incorrect. The asset has not materialization timestamp at all.
    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('does not show historical view alert if `asOf` is past latest materialization', async () => {
      // `act` because we're asserting a null state.
      act(() => {
        render(
          <Test
            path={`/non_sda_asset?asOf=${Number(LatestMaterializationTimestamp) + 1000}`}
            assetKey={{path: ['non_sda_asset']}}
          />,
        );
      });
      await waitFor(() => {
        expect(screen.queryByText(MESSAGE)).toBeNull();
      });
    });

    // Test is incorrect. The asset has not materialization timestamp at all.
    // eslint-disable-next-line jest/no-disabled-tests
    it.skip('does not show historical view alert if `asOf` is equal to latest materialization', async () => {
      // `act` because we're asserting a null state.
      act(() => {
        render(
          <Test
            path={`/non_sda_asset?asOf=${LatestMaterializationTimestamp}`}
            assetKey={{path: ['non_sda_asset']}}
          />,
        );
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });

    it('does not show historical view alert if no `asOf` is specified', async () => {
      // `act` because we're asserting a null state.
      act(() => {
        render(<Test path="/non_sda_asset" assetKey={{path: ['non_sda_asset']}} />);
      });
      expect(screen.queryByText(MESSAGE)).toBeNull();
    });
  });
});
