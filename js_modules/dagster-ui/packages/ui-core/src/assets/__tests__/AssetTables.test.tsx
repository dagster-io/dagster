import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router';
import {RecoilRoot} from 'recoil';

import {mockViewportClientRect, restoreViewportClientRect} from '../../testing/mocking';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {AssetsCatalogTable} from '../AssetsCatalogTable';
import {
  AssetCatalogGroupTableMock,
  AssetCatalogTableMock,
  SingleAssetQueryLastRunFailed,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryTrafficDashboard,
} from '../__fixtures__/AssetTables.fixtures';

const workspaceMocks = buildWorkspaceMocks([]);

const MOCKS = [
  AssetCatalogTableMock,
  AssetCatalogGroupTableMock,
  SingleAssetQueryTrafficDashboard,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryLastRunFailed,
  ...workspaceMocks,
];

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

describe('AssetTable', () => {
  beforeAll(() => {
    mockViewportClientRect();
  });

  afterAll(() => {
    restoreViewportClientRect();
  });

  describe('Materialize button', () => {
    it('is enabled when rows are selected', async () => {
      const Test = () => {
        return (
          <RecoilRoot>
            <MemoryRouter>
              <MockedProvider mocks={MOCKS}>
                <WorkspaceProvider>
                  <AssetsCatalogTable prefixPath={[]} setPrefixPath={() => {}} />
                </WorkspaceProvider>
              </MockedProvider>
            </MemoryRouter>
          </RecoilRoot>
        );
      };
      render(<Test />);

      expect(await screen.findByTestId('materialize-button')).toBeDisabled();
      expect(await screen.findByTestId('materialize-button')).toHaveTextContent(
        'Materialize selected',
      );

      const row1 = await screen.findByTestId(`row-good_asset`);
      const checkbox1 = row1.querySelector('input[type=checkbox]') as HTMLInputElement;
      await userEvent.click(checkbox1);

      expect(await screen.findByTestId('materialize-button')).toHaveTextContent('Materialize');

      const row2 = await screen.findByTestId(`row-late_asset`);
      const checkbox2 = row2.querySelector('input[type=checkbox]') as HTMLInputElement;
      await userEvent.click(checkbox2);

      expect(await screen.findByTestId('materialize-button')).toBeEnabled();

      expect(await screen.findByTestId('materialize-button')).toHaveTextContent(
        'Materialize selected (2)',
      );
    });
  });
});
