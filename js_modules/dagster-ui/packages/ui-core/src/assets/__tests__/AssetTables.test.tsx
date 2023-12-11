import {MockedProvider} from '@apollo/client/testing';
import {render, screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import {MemoryRouter} from 'react-router';

import {AssetsCatalogTable} from '../AssetsCatalogTable';
import {
  AssetCatalogGroupTableMock,
  AssetCatalogTableMock,
  SingleAssetQueryLastRunFailed,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryTrafficDashboard,
} from '../__fixtures__/AssetTables.fixtures';

const MOCKS = [
  AssetCatalogTableMock,
  AssetCatalogGroupTableMock,
  SingleAssetQueryTrafficDashboard,
  SingleAssetQueryMaterializedWithLatestRun,
  SingleAssetQueryMaterializedStaleAndLate,
  SingleAssetQueryLastRunFailed,
];

// This file must be mocked because Jest can't handle `import.meta.url`.
jest.mock('../../graph/asyncGraphLayout', () => ({}));

describe('AssetTable', () => {
  let nativeGBRC: any;

  beforeAll(() => {
    nativeGBRC = window.Element.prototype.getBoundingClientRect;
    window.Element.prototype.getBoundingClientRect = jest
      .fn()
      .mockReturnValue({height: 400, width: 400});
  });

  afterAll(() => {
    window.Element.prototype.getBoundingClientRect = nativeGBRC;
  });

  describe('Materialize button', () => {
    it('is enabled when rows are selected', async () => {
      const Test = () => {
        return (
          <MemoryRouter>
            <MockedProvider mocks={MOCKS}>
              <AssetsCatalogTable prefixPath={['dashboards']} setPrefixPath={() => {}} />
            </MockedProvider>
          </MemoryRouter>
        );
      };
      render(<Test />);

      expect(await screen.findByTestId('materialize-button')).toBeDisabled();
      expect(await screen.findByTestId('materialize-button')).toHaveTextContent(
        'Materialize selected',
      );

      const row1 = await screen.findByTestId(`row-dashboards/cost_dashboard`);
      const checkbox1 = row1.querySelector('input[type=checkbox]') as HTMLInputElement;
      await userEvent.click(checkbox1);

      expect(await screen.findByTestId('materialize-button')).toHaveTextContent('Materialize');

      const row2 = await screen.findByTestId(`row-dashboards/traffic_dashboard`);
      const checkbox2 = row2.querySelector('input[type=checkbox]') as HTMLInputElement;
      await userEvent.click(checkbox2);

      expect(await screen.findByTestId('materialize-button')).toHaveTextContent('Materialize (2)');
    });
  });
});
