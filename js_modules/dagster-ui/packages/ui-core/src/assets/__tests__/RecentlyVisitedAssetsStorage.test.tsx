import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import Router, {MemoryRouter} from 'react-router-dom';

import {AnalyticsContext} from '../../app/analytics';
import {AssetLiveDataProvider} from '../../asset-data/AssetLiveDataProvider';
import {buildAsset, buildAssetConnection, buildAssetKey} from '../../graphql/types';
import {buildQueryMock} from '../../testing/mocking';
import AssetsCatalogRoot, {ASSETS_CATALOG_ROOT_QUERY} from '../AssetsCatalogRoot';
import {ASSET_CATALOG_TABLE_QUERY} from '../AssetsCatalogTable';
import {fetchRecentlyVisitedAssetsFromLocalStorage} from '../RecentlyVisitedAssetsStorage';
import {
  AssetsCatalogRootQuery,
  AssetsCatalogRootQueryVariables,
} from '../types/AssetsCatalogRoot.types';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../types/AssetsCatalogTable.types';

// Mock the `useParams` hook to override the asset key in the URL.
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: jest.fn(),
}));

describe('RecentlyVisitedAssetsStorage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('Store visited asset in local storage', async () => {
    // Set the asset key in the URL
    jest.spyOn(Router, 'useParams').mockReturnValue({0: 'sda_asset'});

    const assetKey = {path: ['sda_asset']};
    const TestAssetView = (
      <MockedProvider
        mocks={[
          buildQueryMock<AssetsCatalogRootQuery, AssetsCatalogRootQueryVariables>({
            query: ASSETS_CATALOG_ROOT_QUERY,
            variables: {
              assetKey,
            },
            data: {
              assetOrError: buildAsset({
                key: buildAssetKey(assetKey),
              }),
            },
          }),
        ]}
      >
        <AnalyticsContext.Provider value={{page: () => {}} as any}>
          <AssetLiveDataProvider>
            <MemoryRouter initialEntries={['/assets/sda_asset']}>
              <AssetsCatalogRoot />
            </MemoryRouter>
          </AssetLiveDataProvider>
        </AnalyticsContext.Provider>
      </MockedProvider>
    );

    // First render displays the page in a loading state
    const {rerender} = render(TestAssetView);
    // Assert that the asset is not stored if the page is still loading
    expect(fetchRecentlyVisitedAssetsFromLocalStorage()).toEqual([]);
    // Wait for the page to load
    await waitFor(() => {
      expect(screen.queryByText('Loading assets…')).toBeNull();
    });
    // Second render displays the page in a loaded state
    // Effect called to store asset in local storage
    rerender(TestAssetView);

    expect(fetchRecentlyVisitedAssetsFromLocalStorage()).toEqual([assetKey]);
  });

  it('Do not store nonexistent asset in local storage', async () => {
    // Set the asset key in the URL
    jest.spyOn(Router, 'useParams').mockReturnValue({0: 'nonexistent_asset'});

    const assetKey = {path: ['nonexistent_asset']};
    const TestAssetView = (
      <MockedProvider
        mocks={[
          buildQueryMock<AssetsCatalogRootQuery, AssetsCatalogRootQueryVariables>({
            query: ASSETS_CATALOG_ROOT_QUERY,
            variables: {
              assetKey,
            },
            data: {
              assetOrError: {
                __typename: 'AssetNotFoundError',
              },
            },
          }),
          buildQueryMock<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>({
            query: ASSET_CATALOG_TABLE_QUERY,
            data: {
              assetsOrError: buildAssetConnection({
                nodes: new Array(12).fill(buildAsset()),
              }),
            },
          }),
        ]}
      >
        <AnalyticsContext.Provider value={{page: () => {}} as any}>
          <AssetLiveDataProvider>
            <MemoryRouter initialEntries={['/assets/nonexistent_asset']}>
              <AssetsCatalogRoot />
            </MemoryRouter>
          </AssetLiveDataProvider>
        </AnalyticsContext.Provider>
      </MockedProvider>
    );

    // First render displays the page in a loading state
    const {rerender} = render(TestAssetView);
    // Assert that the asset is not stored if the page is still loading
    expect(fetchRecentlyVisitedAssetsFromLocalStorage()).toEqual([]);
    // Wait for the page to load
    await waitFor(() => {
      expect(screen.queryByText('Loading assets…')).toBeNull();
    });
    // Second render displays the page in a loaded state
    // Effect called to store asset in local storage
    rerender(TestAssetView);

    expect(fetchRecentlyVisitedAssetsFromLocalStorage()).toEqual([]);
  });
});
