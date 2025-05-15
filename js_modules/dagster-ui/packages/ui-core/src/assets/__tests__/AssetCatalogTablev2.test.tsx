import {MockedProvider} from '@apollo/client/testing';
import {render, screen, waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {RecoilRoot} from 'recoil';
import {FeatureFlag} from 'shared/app/FeatureFlags.oss';

import {setFeatureFlags} from '../../app/Flags';
import {ASSETS_HEALTH_INFO_QUERY} from '../../asset-data/AssetHealthDataProvider';
import {AssetLiveDataProvider, __resetForJest} from '../../asset-data/AssetLiveDataProvider';
import {buildMockedAssetGraphLiveQuery} from '../../asset-data/__tests__/util';
import {
  AssetHealthQuery,
  AssetHealthQueryVariables,
} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionInput} from '../../asset-selection/input/useAssetSelectionInput';
import {
  AssetHealthStatus,
  AssetKey,
  buildAsset,
  buildAssetConnection,
  buildAssetHealth,
  buildAssetKey,
  buildAssetRecord,
  buildAssetRecordConnection,
} from '../../graphql/types';
import {buildQueryMock, getMockResultFn} from '../../testing/mocking';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {AssetCatalogTableV2} from '../catalog/AssetCatalogTableV2';
import {AssetCatalogV2VirtualizedTable} from '../catalog/AssetCatalogV2VirtualizedTable';
import {AssetRecordsQuery, AssetRecordsQueryVariables} from '../types/useAllAssets.types';
import {ASSET_RECORDS_QUERY, AssetRecord} from '../useAllAssets';

setFeatureFlags({[FeatureFlag.flagUseNewObserveUIs]: true});

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

jest.mock('../catalog/AssetCatalogV2VirtualizedTable', () => ({
  AssetCatalogV2VirtualizedTable: jest.fn(() => null),
}));

const createMock = ({
  nodes,
  returnedCursor,
}: {
  returnedCursor: string | null;
  nodes: AssetRecord[];
}) =>
  buildQueryMock<AssetRecordsQuery, AssetRecordsQueryVariables>({
    query: ASSET_RECORDS_QUERY,
    variableMatcher: () => true,
    data: {
      assetRecordsOrError: buildAssetRecordConnection({
        assets: nodes,
        cursor: returnedCursor,
      }),
    },
    delay: 100,
    maxUsageCount: 100,
  });

const assetsMock = createMock({
  nodes: [
    buildAssetRecord({id: 'asset1', key: buildAssetKey({path: ['asset1']})}),
    buildAssetRecord({id: 'asset2', key: buildAssetKey({path: ['asset2']})}),
    buildAssetRecord({id: 'asset3', key: buildAssetKey({path: ['asset3']})}),
    buildAssetRecord({id: 'asset4', key: buildAssetKey({path: ['asset4']})}),
    buildAssetRecord({id: 'asset5', key: buildAssetKey({path: ['asset5']})}),
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
      assetsOrError: buildAssetConnection({
        nodes: assetKeys.map((assetKey, idx) =>
          buildAsset({
            key: assetKey,
            assetHealth: buildAssetHealth({
              assetHealth: statuses[idx % statuses.length],
            }),
          }),
        ),
      }),
    },
  });

const workspaceMocks = buildWorkspaceMocks([]);

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
                ...workspaceMocks,
              ]}
            >
              <WorkspaceProvider>
                <AssetLiveDataProvider>
                  <AssetCatalogTableV2 isFullScreen={false} toggleFullScreen={() => {}} />
                </AssetLiveDataProvider>
              </WorkspaceProvider>
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
        healthDataLoading: false,
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
                ...workspaceMocks,
              ]}
            >
              <WorkspaceProvider>
                <AssetLiveDataProvider>
                  <AssetCatalogTableV2 isFullScreen={false} toggleFullScreen={() => {}} />
                </AssetLiveDataProvider>
              </WorkspaceProvider>
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
        healthDataLoading: false,
      },
      {},
    );
  });
});
