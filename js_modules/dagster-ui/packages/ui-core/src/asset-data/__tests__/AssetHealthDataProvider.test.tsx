import {MockedProvider} from '@apollo/client/testing';
import {renderHook, waitFor} from '@testing-library/react';

import {tokenForAssetKey} from '../../asset-graph/Utils';
import {buildAssetKey} from '../../graphql/types';

// Mock useAllAssetsNodes
const mockUseAllAssetsNodes = jest.fn();
jest.mock('../../assets/useAllAssets', () => ({
  useAllAssetsNodes: mockUseAllAssetsNodes,
}));

// Mock useBlockTraceUntilTrue
const mockUseBlockTraceUntilTrue = jest.fn();
jest.mock('../../performance/TraceContext', () => ({
  useBlockTraceUntilTrue: mockUseBlockTraceUntilTrue,
}));

describe('AssetHealthDataProvider integration tests', () => {
  let useAssetHealthData: any;
  let useAssetsHealthDataWithoutGateCheck: any;
  let __resetForJest: any;

  beforeAll(() => {
    // Import this after mocks are setup
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const module = require('../AssetHealthDataProvider');
    useAssetHealthData = module.useAssetHealthData;
    useAssetsHealthDataWithoutGateCheck = module.useAssetsHealthDataWithoutGateCheck;
    __resetForJest = module.__resetForJest;
  });

  beforeEach(() => {
    mockUseAllAssetsNodes.mockReturnValue({
      allAssetKeys: new Set(),
      loading: false,
    });
    mockUseBlockTraceUntilTrue.mockImplementation(() => {});
  });

  afterEach(() => {
    jest.clearAllMocks();
    __resetForJest();
  });

  describe('useAssetHealthData behavior', () => {
    it('should handle assets without definitions differently than assets with definitions', async () => {
      const assetWithDefinition = buildAssetKey({path: ['asset_with_def']});
      const assetWithoutDefinition = buildAssetKey({path: ['asset_without_def']});

      // Mock that only one asset has a definition
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(assetWithDefinition)]),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      // Test asset with definition
      const {result: resultWithDef} = renderHook(() => useAssetHealthData(assetWithDefinition), {
        wrapper,
      });

      // Test asset without definition
      const {result: resultWithoutDef} = renderHook(
        () => useAssetHealthData(assetWithoutDefinition),
        {wrapper},
      );

      await waitFor(() => {
        // Asset without definition should get an empty fragment
        expect(resultWithoutDef.current.liveData).toEqual({
          __typename: 'Asset',
          key: expect.objectContaining({
            __typename: 'AssetKey',
            path: ['asset_without_def'],
          }),
          latestMaterializationTimestamp: null,
          latestFailedToMaterializeTimestamp: null,
          freshnessStatusChangedTimestamp: null,
          latestCheckWarningTimestamp: null,
          latestCheckFailureTimestamp: null,
          assetHealth: null,
        });
      });

      // Both should complete without errors
      expect(resultWithDef.current.error).toBeFalsy();
      expect(resultWithoutDef.current.error).toBeFalsy();
    });

    it('should use skip parameter correctly based on asset definitions', () => {
      const assetKey = buildAssetKey({path: ['test_asset']});

      // Mock that asset has no definition
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      renderHook(() => useAssetHealthData(assetKey), {wrapper});

      // Verify that skip was passed as true to useBlockTraceUntilTrue
      expect(mockUseBlockTraceUntilTrue).toHaveBeenCalledWith(
        'useAssetHealthData',
        expect.any(Boolean),
        {skip: true},
      );
    });
  });

  describe('useAssetsHealthDataWithoutGateCheck behavior', () => {
    it('should handle mixed assets (some with definitions, some without)', async () => {
      const assetWithDef1 = buildAssetKey({path: ['asset1']});
      const assetWithDef2 = buildAssetKey({path: ['asset2']});
      const assetWithoutDef1 = buildAssetKey({path: ['asset3']});
      const assetWithoutDef2 = buildAssetKey({path: ['asset4']});

      // Mock that only asset1 and asset2 have definitions
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(assetWithDef1), tokenForAssetKey(assetWithDef2)]),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      const {result} = renderHook(
        () =>
          useAssetsHealthDataWithoutGateCheck({
            assetKeys: [assetWithDef1, assetWithDef2, assetWithoutDef1, assetWithoutDef2],
          }),
        {wrapper},
      );

      await waitFor(() => {
        // Should have data for at least the assets without definitions (empty fragments)
        expect(Object.keys(result.current.liveDataByNode).length).toBeGreaterThanOrEqual(2);

        // Assets without definitions should have empty fragments
        expect(result.current.liveDataByNode[tokenForAssetKey(assetWithoutDef1)]).toEqual({
          __typename: 'Asset',
          key: expect.objectContaining({
            __typename: 'AssetKey',
            path: ['asset3'],
          }),
          latestMaterializationTimestamp: null,
          latestFailedToMaterializeTimestamp: null,
          freshnessStatusChangedTimestamp: null,
          latestCheckWarningTimestamp: null,
          latestCheckFailureTimestamp: null,
          assetHealth: null,
        });

        expect(result.current.liveDataByNode[tokenForAssetKey(assetWithoutDef2)]).toEqual({
          __typename: 'Asset',
          key: expect.objectContaining({
            __typename: 'AssetKey',
            path: ['asset4'],
          }),
          latestMaterializationTimestamp: null,
          latestFailedToMaterializeTimestamp: null,
          freshnessStatusChangedTimestamp: null,
          latestCheckWarningTimestamp: null,
        latestCheckFailureTimestamp: null,
          assetHealth: null,
        });
      });
    });

    it('should handle case where no assets have definitions', async () => {
      const asset1 = buildAssetKey({path: ['asset1']});
      const asset2 = buildAssetKey({path: ['asset2']});

      // Mock that no assets have definitions
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      const {result} = renderHook(
        () =>
          useAssetsHealthDataWithoutGateCheck({
            assetKeys: [asset1, asset2],
          }),
        {wrapper},
      );

      await waitFor(() => {
        // Should have empty fragments for both assets
        expect(Object.keys(result.current.liveDataByNode)).toHaveLength(2);

        expect(result.current.liveDataByNode[tokenForAssetKey(asset1)]).toEqual({
          __typename: 'Asset',
          key: expect.objectContaining({
            __typename: 'AssetKey',
            path: ['asset1'],
          }),
          latestMaterializationTimestamp: null,
          latestFailedToMaterializeTimestamp: null,
          freshnessStatusChangedTimestamp: null,
          assetHealth: null,
        });

        expect(result.current.liveDataByNode[tokenForAssetKey(asset2)]).toEqual({
          __typename: 'Asset',
          key: expect.objectContaining({
            __typename: 'AssetKey',
            path: ['asset2'],
          }),
          latestMaterializationTimestamp: null,
          latestFailedToMaterializeTimestamp: null,
          freshnessStatusChangedTimestamp: null,
          latestCheckWarningTimestamp: null,
          latestCheckFailureTimestamp: null,
          assetHealth: null,
        });
      });
    });

    it('should handle loading state correctly', () => {
      const asset = buildAssetKey({path: ['asset1']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(asset)]),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      // Test with loading = true
      renderHook(
        () =>
          useAssetsHealthDataWithoutGateCheck({
            assetKeys: [asset],
            loading: true,
          }),
        {wrapper},
      );

      // Should pass false to useBlockTraceUntilTrue when loading
      expect(mockUseBlockTraceUntilTrue).toHaveBeenCalledWith('useAssetsHealthData', false, {
        skip: false,
      });
    });

    it('should handle blockTrace parameter correctly', () => {
      const asset = buildAssetKey({path: ['asset1']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set([tokenForAssetKey(asset)]),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      // Test with blockTrace = false
      renderHook(
        () =>
          useAssetsHealthDataWithoutGateCheck({
            assetKeys: [asset],
            blockTrace: false,
          }),
        {wrapper},
      );

      expect(mockUseBlockTraceUntilTrue).toHaveBeenCalled();
    });

    it('should handle empty asset keys array', async () => {
      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      const {result} = renderHook(
        () =>
          useAssetsHealthDataWithoutGateCheck({
            assetKeys: [],
          }),
        {wrapper},
      );

      await waitFor(() => {
        expect(Object.keys(result.current.liveDataByNode)).toHaveLength(0);
      });
    });
  });

  describe('edge cases', () => {
    it('should handle complex asset key paths', async () => {
      const complexAsset = buildAssetKey({path: ['namespace', 'deeply', 'nested', 'asset']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      const {result} = renderHook(() => useAssetHealthData(complexAsset), {wrapper});

      await waitFor(() => {
        expect(result.current.liveData).toEqual({
          __typename: 'Asset',
          key: expect.objectContaining({
            __typename: 'AssetKey',
            path: ['namespace', 'deeply', 'nested', 'asset'],
          }),
          latestMaterializationTimestamp: null,
          latestFailedToMaterializeTimestamp: null,
          freshnessStatusChangedTimestamp: null,
          latestCheckWarningTimestamp: null,
          latestCheckFailureTimestamp: null,
          assetHealth: null,
        });
      });
    });

    it('should handle asset keys with special characters', async () => {
      const specialAsset = buildAssetKey({path: ['asset-with-dashes', 'asset_with_underscores']});

      mockUseAllAssetsNodes.mockReturnValue({
        allAssetKeys: new Set(),
        loading: false,
      });

      const wrapper = ({children}: {children: React.ReactNode}) => (
        <MockedProvider>{children}</MockedProvider>
      );

      const {result} = renderHook(() => useAssetHealthData(specialAsset), {wrapper});

      await waitFor(() => {
        expect(result.current.liveData).toEqual({
          __typename: 'Asset',
          key: expect.objectContaining({
            __typename: 'AssetKey',
            path: ['asset-with-dashes', 'asset_with_underscores'],
          }),
          latestMaterializationTimestamp: null,
          latestFailedToMaterializeTimestamp: null,
          freshnessStatusChangedTimestamp: null,
          latestCheckWarningTimestamp: null,
          latestCheckFailureTimestamp: null,
          assetHealth: null,
        });
      });
    });
  });
});
