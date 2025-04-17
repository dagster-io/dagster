import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {RecoilRoot} from 'recoil';

import {ASSETS_HEALTH_INFO_QUERY} from '../../asset-data/AssetHealthDataProvider';
import {AssetLiveDataProvider, __resetForJest} from '../../asset-data/AssetLiveDataProvider';
import {buildMockedAssetGraphLiveQuery} from '../../asset-data/__tests__/util';
import {
  AssetHealthQuery,
  AssetHealthQueryVariables,
} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionInput} from '../../asset-selection/input/useAssetSelectionInput';
import {
  Asset,
  AssetHealthStatus,
  AssetKey,
  buildAsset,
  buildAssetConnection,
  buildAssetHealth,
  buildAssetKey,
  buildAssetNode,
} from '../../graphql/types';
import {buildQueryMock, getMockResultFn} from '../../testing/mocking';
import {AssetCatalogTableV2} from '../AssetCatalogTableV2';
import {AssetCatalogV2VirtualizedTable} from '../AssetCatalogV2VirtualizedTable';
import {ASSET_CATALOG_TABLE_QUERY} from '../AssetsCatalogTable';
import {
  AssetCatalogTableQuery,
  AssetCatalogTableQueryVariables,
} from '../types/AssetsCatalogTable.types';

jest.mock('../../util/idb-lru-cache', () => {
  const mockedCache = {
    has: jest.fn(),
    get: jest.fn(),
    set: jest.fn(),
    constructorArgs: {},
  };

  return {
    cache: (...args: any[]) => {
      mockedCache.constructorArgs = args;
      return mockedCache;
    },
  };
});

jest.mock('../AssetCatalogV2VirtualizedTable', () => ({
  AssetCatalogV2VirtualizedTable: jest.fn(() => null),
}));

const createMock = ({nodes, returnedCursor}: {returnedCursor: string | null; nodes: Asset[]}) =>
  buildQueryMock<AssetCatalogTableQuery, AssetCatalogTableQueryVariables>({
    query: ASSET_CATALOG_TABLE_QUERY,
    variableMatcher: () => true,
    data: {
      assetsOrError: buildAssetConnection({
        nodes,
        cursor: returnedCursor,
      }),
    },
    delay: 100,
    maxUsageCount: 100,
  });

const assetsMock = createMock({
  nodes: [
    buildAsset({key: buildAssetKey({path: ['asset1']})}),
    buildAsset({key: buildAssetKey({path: ['asset2']})}),
    buildAsset({key: buildAssetKey({path: ['asset3']})}),
    buildAsset({key: buildAssetKey({path: ['asset4']})}),
    buildAsset({key: buildAssetKey({path: ['asset5']})}),
  ],
  returnedCursor: '-1',
});

let mockFavorites: undefined | Set<string> = undefined;
jest.mock('shared/assets/useFavoriteAssets.oss', () => ({
  useFavoriteAssets: jest.fn(() => ({
    favorites: mockFavorites,
    loading: false,
  })),
}));

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

afterEach(() => {
  __resetForJest();
  mockFavorites = undefined;
  jest.clearAllMocks();
});

const statuses = [
  AssetHealthStatus.HEALTHY,
  AssetHealthStatus.DEGRADED,
  AssetHealthStatus.WARNING,
  AssetHealthStatus.UNKNOWN,
];
const getHealthQueryMock = (assetKeys: AssetKey[]) =>
  buildQueryMock<AssetHealthQuery, AssetHealthQueryVariables>({
    query: ASSETS_HEALTH_INFO_QUERY,
    variableMatcher: () => true,
    data: {
      assetNodes: assetKeys.map((assetKey, idx) =>
        buildAssetNode({
          assetKey,
          assetHealth: buildAssetHealth({
            assetHealth: statuses[idx % statuses.length],
          }),
        }),
      ),
    },
  });

describe('AssetCatalogTableV2', () => {
  it('renders', async () => {
    const assetKeys = [
      buildAssetKey({path: ['asset1']}),
      buildAssetKey({path: ['asset2']}),
      buildAssetKey({path: ['asset3']}),
      buildAssetKey({path: ['asset4']}),
      buildAssetKey({path: ['asset5']}),
    ];
    const healthQueryMock = getHealthQueryMock(assetKeys);
    const resultFn = getMockResultFn(healthQueryMock);
    expect(() =>
      render(
        <RecoilRoot>
          <MemoryRouter>
            <MockedProvider
              mocks={[
                assetsMock,
                healthQueryMock,
                ...buildMockedAssetGraphLiveQuery(assetKeys, undefined),
              ]}
            >
              <AssetLiveDataProvider>
                <AssetCatalogTableV2 isFullScreen={false} toggleFullScreen={() => {}} />
              </AssetLiveDataProvider>
            </MockedProvider>
          </MemoryRouter>
        </RecoilRoot>,
      ),
    ).not.toThrow();

    await waitFor(() => {
      expect(screen.getByText('5 assets')).toBeInTheDocument();
      expect(resultFn).toHaveBeenCalled();
    });
    const calls = (AssetCatalogV2VirtualizedTable as unknown as jest.Mock).mock.calls;
    await waitFor(() => {
      expect(calls[calls.length - 1][0]).toEqual({
        groupedByStatus: {
          Healthy: [
            expect.objectContaining({assetKey: buildAssetKey({path: ['asset1']})}),
            expect.objectContaining({assetKey: buildAssetKey({path: ['asset5']})}),
          ],
          Degraded: [expect.objectContaining({assetKey: buildAssetKey({path: ['asset2']})})],
          Warning: [expect.objectContaining({assetKey: buildAssetKey({path: ['asset3']})})],
          Unknown: [expect.objectContaining({assetKey: buildAssetKey({path: ['asset4']})})],
        },
        loading: false,
      });
    });
  });

  it('renders with favorites and ignores results from useAllAssets', async () => {
    mockFavorites = new Set(['asset1', 'asset2']);
    const assetKeys = [buildAssetKey({path: ['asset1']}), buildAssetKey({path: ['asset2']})];
    const healthQueryMock = getHealthQueryMock(assetKeys);
    const resultFn = getMockResultFn(healthQueryMock);
    expect(() =>
      render(
        <RecoilRoot>
          <MemoryRouter>
            <MockedProvider
              mocks={[
                assetsMock,
                healthQueryMock,
                ...buildMockedAssetGraphLiveQuery(assetKeys, undefined),
              ]}
            >
              <AssetLiveDataProvider>
                <AssetCatalogTableV2 isFullScreen={false} toggleFullScreen={() => {}} />
              </AssetLiveDataProvider>
            </MockedProvider>
          </MemoryRouter>
        </RecoilRoot>,
      ),
    ).not.toThrow();

    await waitFor(() => {
      expect(screen.getByText('2 assets')).toBeInTheDocument();
      expect(resultFn).toHaveBeenCalled();
    });
    expect(AssetCatalogV2VirtualizedTable).toHaveBeenCalledWith(
      {
        groupedByStatus: {
          Healthy: [expect.objectContaining({assetKey: buildAssetKey({path: ['asset1']})})],
          Degraded: [expect.objectContaining({assetKey: buildAssetKey({path: ['asset2']})})],
          Warning: [],
          Unknown: [],
        },
        loading: false,
      },
      {},
    );
  });
});
