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
} from '../../graphql/types';
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

jest.mock('shared/asset-selection/input/useAssetSelectionInput', () => {
  const mock: typeof useAssetSelectionInput = ({
    assets,
    assetsLoading,
  }: {
    assets: any;
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
      const {findByTestId, findAllByRole} = render(
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

      await waitFor(async () => {
        const checkboxes = await findAllByRole('checkbox');
        const goodAssetCheckbox = await findByTestId('checkbox-good_asset');
        expect(checkboxes.indexOf(goodAssetCheckbox)).toBe(1);
      });

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
