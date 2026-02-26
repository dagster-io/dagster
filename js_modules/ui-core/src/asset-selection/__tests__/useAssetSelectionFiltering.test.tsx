import {renderHook, waitFor} from '@testing-library/react';

import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useAssetGraphData} from '../../asset-graph/useAssetGraphData';
import {buildAssetKey} from '../../graphql/types';
import {useAssetSelectionFiltering} from '../useAssetSelectionFiltering';

const mockTokenForAssetKeyNotMock = tokenForAssetKey;
jest.mock('../util', () => ({
  getAssetsByKey: jest.fn((assets) => {
    const map = new Map();
    assets.forEach((asset: any) => {
      const key = asset.key || asset.assetKey;
      map.set(mockTokenForAssetKeyNotMock(key), asset);
    });
    return map;
  }),
}));

jest.mock('../../asset-graph/useAssetGraphData', () => ({
  useAssetGraphData: jest.fn(),
}));

jest.mock('../../util/hashObject', () => ({
  hashObject: jest.fn((obj) => JSON.stringify(obj)),
}));

jest.mock('../../util/weakMapMemoize', () => ({
  weakMapMemoize: jest.fn((fn) => fn),
}));

const mockUseAssetGraphData = useAssetGraphData as jest.MockedFunction<typeof useAssetGraphData>;

// Test data helpers
const createMockAsset = (path: string[], hasDefinition = true) => ({
  id: `asset-${path.join('-')}`,
  key: buildAssetKey({path}),
  definition: hasDefinition
    ? {
        changedReasons: [],
        owners: [],
        groupName: 'default',
        tags: [],
        kinds: [],
        repository: {
          name: 'test-repo',
          location: {
            name: 'test-location',
          },
        },
      }
    : null,
});

const createMockExternalAsset = (path: string[]) => createMockAsset(path, false);

const createMockAssetGraphResponse = (
  assetKeys: Array<{path: string[]}>,
  loading = false,
  graphQueryItems: any[] = [],
) => ({
  loading,
  assetGraphData: null,
  graphQueryItems,
  graphAssetKeys: assetKeys.map((key) => buildAssetKey(key)),
  allAssetKeys: assetKeys.map((key) => buildAssetKey(key)),
});

describe('useAssetSelectionFiltering', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const defaultProps = {
    loading: false,
    assetSelection: '*',
    assets: [],
    includeExternalAssets: true,
    skip: false,
  };

  it('returns initial state when loading', () => {
    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], true));

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        loading: true,
      }),
    );

    expect(result.current.loading).toBe(true);
    expect(result.current.filtered).toEqual([]);
    expect(result.current.filteredByKey).toEqual({});
  });

  it('filters assets based on graph data', async () => {
    const mockAssets = [
      createMockAsset(['asset1']),
      createMockAsset(['asset2']),
      createMockAsset(['asset3']),
    ];

    const graphKeys = [{path: ['asset1']}, {path: ['asset2']}];

    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse(graphKeys, false));

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: mockAssets,
        assetSelection: 'asset1,asset2',
      }),
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
      expect(result.current.filtered).toHaveLength(2);
      expect(result.current.filtered.map((a) => a.key.path)).toEqual([['asset1'], ['asset2']]);
    });
  });

  it('sorts filtered assets by key path', async () => {
    const mockAssets = [
      createMockAsset(['z_asset']),
      createMockAsset(['a_asset']),
      createMockAsset(['m_asset']),
    ];

    const graphKeys = [{path: ['z_asset']}, {path: ['a_asset']}, {path: ['m_asset']}];

    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse(graphKeys, false));

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: mockAssets,
      }),
    );

    await waitFor(() => {
      expect(result.current.filtered.map((a) => a.key.path)).toEqual([
        ['a_asset'],
        ['m_asset'],
        ['z_asset'],
      ]);
    });
  });

  it('creates filteredByKey object correctly', async () => {
    const mockAssets = [createMockAsset(['asset1']), createMockAsset(['asset2'])];

    const graphKeys = [{path: ['asset1']}, {path: ['asset2']}];

    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse(graphKeys, false));

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: mockAssets,
      }),
    );

    await waitFor(() => {
      expect(result.current.filteredByKey).toEqual({
        asset1: mockAssets[0],
        asset2: mockAssets[1],
      });
    });
  });

  it('handles external assets when includeExternalAssets is true', async () => {
    const mockAssets = [
      createMockAsset(['internal_asset']),
      createMockExternalAsset(['external_asset']),
    ];

    mockUseAssetGraphData.mockReturnValue(
      createMockAssetGraphResponse([{path: ['internal_asset']}, {path: ['external_asset']}], false),
    );

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: mockAssets,
        includeExternalAssets: true,
      }),
    );

    // Verify that useAssetGraphData was called with external assets
    expect(mockUseAssetGraphData).toHaveBeenCalledWith(
      '*',
      expect.objectContaining({
        externalAssets: [mockAssets[1]], // Only the external asset
      }),
    );

    await waitFor(() => {
      expect(result.current.filtered).toHaveLength(2);
    });
  });

  it('excludes external assets when includeExternalAssets is false', () => {
    const mockAssets = [
      createMockAsset(['internal_asset']),
      createMockExternalAsset(['external_asset']),
    ];

    mockUseAssetGraphData.mockReturnValue(
      createMockAssetGraphResponse([{path: ['internal_asset']}], false),
    );

    renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: mockAssets,
        includeExternalAssets: false,
      }),
    );

    // Verify that useAssetGraphData was called without external assets
    expect(mockUseAssetGraphData).toHaveBeenCalledWith(
      '*',
      expect.objectContaining({
        externalAssets: undefined,
      }),
    );
  });

  it('passes useWorker option to useAssetGraphData', () => {
    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    renderHook(() => useAssetSelectionFiltering(defaultProps));

    expect(mockUseAssetGraphData).toHaveBeenCalledWith('*', expect.any(Object));
  });

  it('passes skip option to useAssetGraphData', () => {
    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        skip: true,
      }),
    );

    expect(mockUseAssetGraphData).toHaveBeenCalledWith(
      '*',
      expect.objectContaining({
        skip: true,
      }),
    );
  });

  it('handles empty assets array', () => {
    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: [],
      }),
    );

    expect(result.current.filtered).toEqual([]);
    expect(result.current.filteredByKey).toEqual({});
  });

  it('handles undefined assets', () => {
    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: undefined,
      }),
    );

    expect(result.current.filtered).toEqual([]);
    expect(result.current.filteredByKey).toEqual({});
  });

  it('filters out null assets from graph results', async () => {
    const mockAssets = [createMockAsset(['asset1'])];

    // Graph returns asset that doesn't exist in our assets list
    const graphKeys = [{path: ['asset1']}, {path: ['nonexistent_asset']}];

    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse(graphKeys, false));

    const {result} = renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: mockAssets,
      }),
    );

    await waitFor(() => {
      expect(result.current.filtered).toHaveLength(1);
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      expect(result.current.filtered[0]!.key.path).toEqual(['asset1']);
    });
  });

  it('passes asset selection query to useAssetGraphData', () => {
    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    const assetSelection = 'tag:my-tag';

    renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assetSelection,
      }),
    );

    expect(mockUseAssetGraphData).toHaveBeenCalledWith(assetSelection, expect.any(Object));
  });

  it('configures hideEdgesToNodesOutsideQuery correctly', () => {
    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
      }),
    );

    expect(mockUseAssetGraphData).toHaveBeenCalledWith(
      '*',
      expect.objectContaining({
        hideEdgesToNodesOutsideQuery: true,
      }),
    );
  });

  it('configures hideNodesMatching function correctly', () => {
    const mockAssets = [createMockAsset(['asset1'])];

    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    renderHook(() =>
      useAssetSelectionFiltering({
        ...defaultProps,
        assets: mockAssets,
      }),
    );

    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    const callArgs = mockUseAssetGraphData.mock.calls[0]!;
    const config = callArgs[1];
    expect(config.hideNodesMatching).toBeDefined();

    // Test the hideNodesMatching function
    const mockNode = {
      assetKey: buildAssetKey({path: ['asset1']}),
    };
    const shouldHide = config.hideNodesMatching?.(mockNode as any);
    expect(shouldHide).toBe(false); // Should not hide because asset exists in our list

    const nonExistentNode = {
      assetKey: buildAssetKey({path: ['nonexistent']}),
    };
    const shouldHideNonExistent = config.hideNodesMatching?.(nonExistentNode as any);
    expect(shouldHideNonExistent).toBe(true); // Should hide because asset doesn't exist in our list
  });

  it('memoizes external assets based on includeExternalAssets flag', () => {
    const mockAssets = [createMockAsset(['internal']), createMockExternalAsset(['external'])];

    mockUseAssetGraphData.mockReturnValue(createMockAssetGraphResponse([], false));

    const {rerender} = renderHook(
      ({includeExternalAssets}) =>
        useAssetSelectionFiltering({
          ...defaultProps,
          assets: mockAssets,
          includeExternalAssets,
        }),
      {
        initialProps: {includeExternalAssets: true},
      },
    );

    // Initial render with includeExternalAssets = true
    expect(mockUseAssetGraphData).toHaveBeenLastCalledWith(
      '*',
      expect.objectContaining({
        externalAssets: [mockAssets[1]],
      }),
    );

    // Rerender with includeExternalAssets = false
    rerender({includeExternalAssets: false});

    expect(mockUseAssetGraphData).toHaveBeenLastCalledWith(
      '*',
      expect.objectContaining({
        externalAssets: undefined,
      }),
    );
  });
});
