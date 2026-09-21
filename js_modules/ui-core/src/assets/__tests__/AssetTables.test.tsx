import {MockedProvider} from '@apollo/client/testing';
import {render, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router';
import {RecoilRoot} from 'recoil';

import {useAssetSelectionInput} from '../../asset-selection/input/useAssetSelectionInput';
import {
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../graphql/builders';
import {mockViewportClientRect, restoreViewportClientRect} from '../../testing/mocking';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {AssetsCatalogTable} from '../AssetsCatalogTable';
import {
  AssetCatalogTableMock,
  AssetCatalogTableMockAssets,
  SingleAssetQueryLastRunFailed,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryTrafficDashboard,
} from '../__fixtures__/AssetTables.fixtures';

const workspaceMocks = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    locationOrLoadError: buildRepositoryLocation({
      repositories: [
        buildRepository({
          assetNodes: AssetCatalogTableMockAssets.filter((asset) => asset.definition).map(
            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
            (asset) => asset.definition!,
          ),
        }),
      ],
    }),
  }),
]);

const MOCKS = [
  AssetCatalogTableMock,
  SingleAssetQueryTrafficDashboard,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryLastRunFailed,
  ...workspaceMocks,
];

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

jest.mock('../../asset-selection/input/useAssetSelectionInput', () => {
  const mock: typeof useAssetSelectionInput = ({
    assets,
    assetsLoading,
  }: {
    assets: any[];
    assetsLoading?: boolean;
  }) => {
    return {
      filterInput: <div />,
      fetchResult: {loading: false},
      loading: !!assetsLoading,
      filtered: assets,
      assetSelection: '',
      setAssetSelection: () => {},
    };
  };
  return {
    useAssetSelectionInput: mock,
  };
});

describe('AssetTable', () => {
  beforeAll(() => {
    mockViewportClientRect();
  });

  afterAll(() => {
    restoreViewportClientRect();
  });

  describe('Materialize button', () => {
    it('is enabled when rows are selected', async () => {
      const user = userEvent.setup();
      const {findByTestId, getByTestId, getAllByRole} = render(
        <RecoilRoot>
          <MemoryRouter>
            <MockedProvider mocks={MOCKS}>
              <WorkspaceProvider>
                <AssetsCatalogTable prefixPath={[]} setPrefixPath={() => {}} />
              </WorkspaceProvider>
            </MockedProvider>
          </MemoryRouter>
        </RecoilRoot>,
      );

      let materializeButton = await findByTestId('materialize-button');
      expect(materializeButton).toBeDisabled();
      expect(materializeButton).toHaveTextContent('Materialize selected');

      // The asset list renders external (non-SDA) assets in fixture order until
      // the WorkspaceContext query resolves and the software-defined assets
      // (good_asset, late_asset, ...) sort to the front. good_asset only reaches
      // checkbox index 1 (index 0 is the header "select all") once that load
      // completes. On slow CI workers the workspace + asset-records + Apollo
      // render chain can exceed waitFor's default 1000ms timeout, so give it more
      // room. Use synchronous queries inside waitFor rather than nested findBy*,
      // which would compound their own async timeouts.
      await waitFor(
        () => {
          const checkboxes = getAllByRole('checkbox');
          const goodAssetCheckbox = getByTestId('checkbox-good_asset');
          expect(checkboxes.indexOf(goodAssetCheckbox)).toBe(1);
        },
        {timeout: 5000},
      );

      const goodAssetCheckbox = await findByTestId('checkbox-good_asset');
      await user.click(goodAssetCheckbox);

      materializeButton = await findByTestId('materialize-button');
      expect(materializeButton).toHaveTextContent('Materialize');

      const lateAssetCheckbox = await findByTestId('checkbox-late_asset');
      await user.click(lateAssetCheckbox);

      materializeButton = await findByTestId('materialize-button');
      expect(materializeButton).toBeEnabled();
      expect(materializeButton).toHaveTextContent('Materialize selected (2)');
    });
  });
});
