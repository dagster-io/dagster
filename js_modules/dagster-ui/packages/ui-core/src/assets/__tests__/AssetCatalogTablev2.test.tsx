import {MockedProvider} from '@apollo/client/testing';
import {render, waitFor} from '@testing-library/react';
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
  AssetHealthStatus,
  AssetKey,
  buildAsset,
  buildAssetConnection,
  buildAssetHealth,
  buildAssetKey,
  buildAssetNode,
  buildAssetRecord,
  buildAssetRecordConnection,
  buildRepository,
  buildRepositoryLocation,
  buildWorkspaceLocationEntry,
} from '../../graphql/types';
import {buildQueryMock, getMockResultFn} from '../../testing/mocking';
import {WorkspaceProvider} from '../../workspace/WorkspaceContext/WorkspaceContext';
import {buildWorkspaceMocks} from '../../workspace/WorkspaceContext/__fixtures__/Workspace.fixtures';
import {AssetCatalogTableV2} from '../catalog/AssetCatalogTableV2';
import {AssetCatalogV2VirtualizedTable} from '../catalog/AssetCatalogV2VirtualizedTable';
import {AssetRecordsQuery, AssetRecordsQueryVariables} from '../types/useAllAssets.types';
import {ASSET_RECORDS_QUERY, AssetRecord} from '../useAllAssets';

jest.mock('../../app/observeEnabled.oss', () => ({
  observeEnabled: jest.fn(() => true),
}));

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

const asset1 = buildAssetKey({path: ['asset1']});
const asset2 = buildAssetKey({path: ['asset2']});
const asset3 = buildAssetKey({path: ['asset3']});
const asset4 = buildAssetKey({path: ['asset4']});
const asset5 = buildAssetKey({path: ['asset5']});

const assetsMock = createMock({
  nodes: [
    buildAssetRecord({id: 'asset1', key: asset1}),
    buildAssetRecord({id: 'asset2', key: asset2}),
    buildAssetRecord({id: 'asset3', key: asset3}),
    buildAssetRecord({id: 'asset4', key: asset4}),
    buildAssetRecord({id: 'asset5', key: asset5}),
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

const workspaceMocks = buildWorkspaceMocks([
  buildWorkspaceLocationEntry({
    locationOrLoadError: buildRepositoryLocation({
      repositories: [
        buildRepository({
          assetNodes: [
            buildAssetNode({assetKey: asset1}),
            buildAssetNode({assetKey: asset2}),
            buildAssetNode({assetKey: asset3}),
            buildAssetNode({assetKey: asset4}),
            buildAssetNode({assetKey: asset5}),
          ],
        }),
      ],
    }),
  }),
]);

describe('AssetCatalogTableV2', () => {
  it('renders', async () => {
    const assetKeys = [asset1, asset2, asset3, asset4, asset5];
    const healthQueryMock = getHealthQueryMock(assetKeys);
    const resultFn = getMockResultFn(healthQueryMock);
    const {findByText} = render(
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
                <AssetCatalogTableV2 />
              </AssetLiveDataProvider>
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>
      </RecoilRoot>,
    );

    await findByText('5 assets');
    await waitFor(() => {
      expect(resultFn).toHaveBeenCalled();
    });

    await waitFor(() => {
      const calls = (AssetCatalogV2VirtualizedTable as unknown as jest.Mock).mock.calls;
      const props = calls[calls.length - 1][0];
      expect(props).toEqual(
        expect.objectContaining({
          healthDataLoading: false,
        }),
      );
    });

    const calls = (AssetCatalogV2VirtualizedTable as unknown as jest.Mock).mock.calls;
    const props = calls[calls.length - 1][0];
    expect(props).toEqual(
      expect.objectContaining({
        checkedDisplayKeys: new Set(),
        loading: false,
        healthDataLoading: false,
        grouped: expect.objectContaining({
          Healthy: expect.objectContaining({
            assets: [
              expect.objectContaining({key: asset1}),
              expect.objectContaining({key: asset5}),
            ],
          }),
          Degraded: expect.objectContaining({
            assets: [expect.objectContaining({key: asset2})],
          }),
          Warning: expect.objectContaining({
            assets: [expect.objectContaining({key: asset3})],
          }),
          Unknown: expect.objectContaining({
            assets: [expect.objectContaining({key: asset4})],
          }),
        }),
      }),
    );
  });

  it('renders with favorites and ignores results from useAllAssets', async () => {
    mockFavorites = new Set(['asset1', 'asset2']);
    const assetKeys = [buildAssetKey({path: ['asset1']}), buildAssetKey({path: ['asset2']})];
    const healthQueryMock = getHealthQueryMock(assetKeys);
    const resultFn = getMockResultFn(healthQueryMock);
    const {findByText} = render(
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
                <AssetCatalogTableV2 />
              </AssetLiveDataProvider>
            </WorkspaceProvider>
          </MockedProvider>
        </MemoryRouter>
      </RecoilRoot>,
    );

    expect(await findByText('2 assets')).toBeInTheDocument();
    await waitFor(() => {
      expect(resultFn).toHaveBeenCalled();
    });

    await waitFor(() => {
      const calls = (AssetCatalogV2VirtualizedTable as unknown as jest.Mock).mock.calls;
      const props = calls[calls.length - 1][0];
      expect(props).toEqual(
        expect.objectContaining({
          checkedDisplayKeys: new Set(['asset1', 'asset2']),
          loading: false,
          healthDataLoading: false,
          grouped: expect.objectContaining({
            Healthy: expect.objectContaining({
              assets: [expect.objectContaining({key: asset1})],
            }),
            Degraded: expect.objectContaining({
              assets: [expect.objectContaining({key: asset2})],
            }),
          }),
        }),
      );
    });
  });
});
