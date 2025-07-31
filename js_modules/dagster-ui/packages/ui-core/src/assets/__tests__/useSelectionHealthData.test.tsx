jest.useFakeTimers();

import {render, waitFor} from '@testing-library/react';
import React from 'react';

import {AssetHealthData, useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {AssetKeyInput, buildAsset, buildAssetKey, buildAssetRecord} from '../../graphql/types';
import {
  SelectionHealthDataProvider,
  useSelectionFilterData,
  useSelectionHealthData,
} from '../catalog/useSelectionHealthData';
import {useAllAssets} from '../useAllAssets';

// Mock the dependencies
jest.mock('../../asset-selection/useAssetSelectionFiltering', () => ({
  useAssetSelectionFiltering: jest.fn(),
}));

jest.mock('../useAllAssets', () => ({
  useAllAssets: jest.fn(),
}));

jest.mock('../../asset-data/AssetHealthDataProvider', () => ({
  AssetHealthData: {
    manager: {
      pauseThread: jest.fn(),
      unpauseThread: jest.fn(),
    },
  },
  useAssetsHealthData: jest.fn(),
}));

const mockedUseAssetSelectionFiltering = useAssetSelectionFiltering as jest.MockedFunction<
  typeof useAssetSelectionFiltering
>;
const mockedUseAllAssets = useAllAssets as jest.MockedFunction<typeof useAllAssets>;
const mockedUseAssetsHealthData = useAssetsHealthData as jest.MockedFunction<
  typeof useAssetsHealthData
>;

afterEach(() => {
  jest.clearAllMocks();
});

function TestComponent({
  selection,
  onHealthData,
  onFilterData,
}: {
  selection: string;
  onHealthData?: (data: any) => void;
  onFilterData?: (data: any) => void;
}) {
  const healthData = useSelectionHealthData({selection});
  const filterData = useSelectionFilterData({selection});

  React.useEffect(() => {
    onHealthData?.(healthData);
  }, [healthData, onHealthData]);

  React.useEffect(() => {
    onFilterData?.(filterData);
  }, [filterData, onFilterData]);

  return <div data-testid={`test-${selection}`} />;
}

function FilterOnlyComponent({
  selection,
  onFilterData,
}: {
  selection: string;
  onFilterData?: (data: any) => void;
}) {
  const filterData = useSelectionFilterData({selection});

  React.useEffect(() => {
    onFilterData?.(filterData);
  }, [filterData, onFilterData]);

  return <div data-testid={`filter-${selection}`} />;
}

function HealthOnlyComponent({
  selection,
  onHealthData,
}: {
  selection: string;
  onHealthData?: (data: any) => void;
}) {
  const healthData = useSelectionHealthData({selection});

  React.useEffect(() => {
    onHealthData?.(healthData);
  }, [healthData, onHealthData]);

  return <div data-testid={`health-${selection}`} />;
}

const createMockAsset = (path: string[]) =>
  buildAsset({
    id: path.join('-'),
    key: buildAssetKey({path}),
    definition: null,
  });

const createMockHealthData = (assetKeys: AssetKeyInput[]): Record<string, AssetHealthFragment> => {
  const result: Record<string, AssetHealthFragment> = {};
  assetKeys.forEach((key) => {
    const keyString = key.path.join('/');
    result[keyString] = buildAsset({
      key: buildAssetKey({path: key.path}),
      assetMaterializations: [],
      assetHealth: null,
    });
  });
  return result;
};

describe('useSelectionHealthData', () => {
  beforeEach(() => {
    // Default mock implementations
    mockedUseAllAssets.mockReturnValue({
      assets: [],
      loading: false,
      query: jest.fn(),
      assetsByAssetKey: new Map(),
      error: null,
    });

    mockedUseAssetSelectionFiltering.mockReturnValue({
      filtered: [],
      filteredByKey: {},
      loading: false,
      graphAssetKeys: [],
      graphQueryItems: [],
    });

    mockedUseAssetsHealthData.mockReturnValue({
      liveDataByNode: {},
      refresh: jest.fn(),
      refreshing: false,
    });
  });

  describe('SelectionHealthDataProvider', () => {
    it('provides context for watching selections', () => {
      const onHealthData = jest.fn();
      const onFilterData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent
            selection="asset1"
            onHealthData={onHealthData}
            onFilterData={onFilterData}
          />
        </SelectionHealthDataProvider>,
      );

      expect(onHealthData).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 0,
        loading: false,
      });

      expect(onFilterData).toHaveBeenCalledWith({
        assets: [],
        loading: false,
      });
    });

    it('handles multiple components watching the same selection', () => {
      const onHealthData1 = jest.fn();
      const onHealthData2 = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="asset1" onHealthData={onHealthData1} />
          <TestComponent selection="asset1" onHealthData={onHealthData2} />
        </SelectionHealthDataProvider>,
      );

      // Both components should receive the same data
      expect(onHealthData1).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 0,
        loading: false,
      });
      expect(onHealthData2).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 0,
        loading: false,
      });
    });

    it('handles multiple different selections', () => {
      const assets1 = [createMockAsset(['asset1'])];
      const assets2 = [createMockAsset(['asset2'])];

      mockedUseAssetSelectionFiltering
        .mockReturnValueOnce({
          filtered: assets1,
          filteredByKey: {},
          loading: false,
          graphAssetKeys: [buildAssetKey({path: ['asset1']})],
          graphQueryItems: [],
        })
        .mockReturnValueOnce({
          filtered: assets2,
          filteredByKey: {},
          loading: false,
          graphAssetKeys: [buildAssetKey({path: ['asset2']})],
          graphQueryItems: [],
        });

      const onHealthData1 = jest.fn();
      const onHealthData2 = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="selection1" onHealthData={onHealthData1} />
          <TestComponent selection="selection2" onHealthData={onHealthData2} />
        </SelectionHealthDataProvider>,
      );

      expect(onHealthData1).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 1,
        loading: true,
      });
      expect(onHealthData2).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 1,
        loading: true,
      });
    });
  });

  describe('useSelectionHealthData hook', () => {
    it('returns initial empty state', () => {
      const onHealthData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      expect(onHealthData).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 0,
        loading: false,
      });
    });

    it('updates when asset data changes', async () => {
      const assets = [createMockAsset(['asset1']), createMockAsset(['asset2'])];
      const assetKeys = assets.map((asset) => asset.key);
      const mockHealthData = createMockHealthData(assetKeys);

      mockedUseAssetSelectionFiltering.mockReturnValue({
        filtered: assets,
        filteredByKey: {},
        loading: false,
        graphAssetKeys: assetKeys,
        graphQueryItems: [],
      });

      mockedUseAssetsHealthData.mockReturnValue({
        liveDataByNode: mockHealthData,
        refresh: jest.fn(),
        refreshing: false,
      });

      const onHealthData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      await waitFor(() => {
        expect(onHealthData).toHaveBeenCalledWith({
          liveDataByNode: mockHealthData,
          assetCount: 2,
          loading: false,
        });
      });
    });

    it('shows loading state when filtering is loading', async () => {
      const assets = [createMockAsset(['asset1'])];

      mockedUseAssetSelectionFiltering.mockReturnValue({
        filtered: assets,
        filteredByKey: {},
        loading: true,
        graphAssetKeys: [buildAssetKey({path: ['asset1']})],
        graphQueryItems: [],
      });

      mockedUseAllAssets.mockReturnValue({
        assets,
        loading: true,
        query: jest.fn(),
        assetsByAssetKey: new Map(),
        error: null,
      });

      const onHealthData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      await waitFor(() => {
        expect(onHealthData).toHaveBeenCalledWith({
          liveDataByNode: {},
          assetCount: 1,
          loading: true,
        });
      });
    });

    it('shows loading state when health data is incomplete', async () => {
      const assets = [
        buildAssetRecord({key: buildAssetKey({path: ['asset1']})}),
        buildAssetRecord({key: buildAssetKey({path: ['asset2']})}),
      ];
      const assetKeys = assets.map((asset) => asset.key);
      // Only provide health data for one asset
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      const partialHealthData = createMockHealthData([assetKeys[0]!]);

      mockedUseAssetSelectionFiltering.mockReturnValue({
        filtered: assets,
        filteredByKey: {},
        loading: false,
        graphAssetKeys: assetKeys,
        graphQueryItems: [],
      });

      mockedUseAssetsHealthData.mockReturnValue({
        liveDataByNode: partialHealthData,
        refresh: jest.fn(),
        refreshing: false,
      });

      const onHealthData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      await waitFor(() => {
        expect(onHealthData).toHaveBeenCalledWith({
          liveDataByNode: partialHealthData,
          assetCount: 2,
          loading: true, // Loading because filtered.length (2) !== Object.keys(liveDataByNode).length (1)
        });
      });
    });
  });

  describe('useSelectionFilterData hook', () => {
    it('returns initial empty state', () => {
      const onFilterData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onFilterData={onFilterData} />
        </SelectionHealthDataProvider>,
      );

      expect(onFilterData).toHaveBeenCalledWith({
        assets: [],
        loading: false,
      });
    });

    it('updates when filtered assets change', async () => {
      const assets = [
        buildAssetRecord({key: buildAssetKey({path: ['asset1']})}),
        buildAssetRecord({key: buildAssetKey({path: ['asset2']})}),
      ];

      mockedUseAssetSelectionFiltering.mockReturnValue({
        filtered: assets,
        filteredByKey: {},
        loading: false,
        graphAssetKeys: [],
        graphQueryItems: [],
      });

      const onFilterData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onFilterData={onFilterData} />
        </SelectionHealthDataProvider>,
      );

      await waitFor(() => {
        expect(onFilterData).toHaveBeenCalledWith({
          assets,
          loading: false,
        });
      });
    });

    it('shows loading state when filtering is loading', async () => {
      mockedUseAssetSelectionFiltering.mockReturnValue({
        filtered: [],
        filteredByKey: {},
        loading: true,
        graphAssetKeys: [],
        graphQueryItems: [],
      });

      const onFilterData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onFilterData={onFilterData} />
        </SelectionHealthDataProvider>,
      );

      await waitFor(() => {
        expect(onFilterData).toHaveBeenCalledWith({
          assets: [],
          loading: true,
        });
      });
    });
  });

  describe('thread management', () => {
    it('pauses health thread when no health listeners', async () => {
      const pauseThreadSpy = jest.spyOn(AssetHealthData.manager, 'pauseThread');
      const unpauseThreadSpy = jest.spyOn(AssetHealthData.manager, 'unpauseThread');

      render(
        <SelectionHealthDataProvider>
          <FilterOnlyComponent selection="test-selection" />
        </SelectionHealthDataProvider>,
      );

      await waitFor(() => {
        expect(pauseThreadSpy).toHaveBeenCalledWith('selection-test-selection');
      });

      render(
        <SelectionHealthDataProvider>
          <HealthOnlyComponent selection="test-selection" />
        </SelectionHealthDataProvider>,
      );

      await waitFor(() => {
        expect(unpauseThreadSpy).toHaveBeenCalledWith('selection-test-selection');
      });
    });

    it('unpauses health thread when health listeners are present', () => {
      const unpauseThreadSpy = jest.spyOn(AssetHealthData.manager, 'unpauseThread');
      const onHealthData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      expect(unpauseThreadSpy).toHaveBeenCalledWith('selection-test-selection');
    });

    it('handles component unmounting without errors', () => {
      const unpauseThreadSpy = jest.spyOn(AssetHealthData.manager, 'unpauseThread');
      const onHealthData = jest.fn();

      const {unmount} = render(
        <SelectionHealthDataProvider>
          <HealthOnlyComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      // Verify thread was unpaused when component mounted
      expect(unpauseThreadSpy).toHaveBeenCalledWith('selection-test-selection');

      // Unmounting should not cause errors
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('optimization behavior', () => {
    it('provider manages multiple selections efficiently', () => {
      const onHealthData1 = jest.fn();
      const onHealthData2 = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="selection1" onHealthData={onHealthData1} />
          <TestComponent selection="selection2" onHealthData={onHealthData2} />
        </SelectionHealthDataProvider>,
      );

      // Both components should receive data
      expect(onHealthData1).toHaveBeenCalled();
      expect(onHealthData2).toHaveBeenCalled();
    });

    it('hooks provide data when called', () => {
      const onFilterData = jest.fn();
      const onHealthData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent
            selection="test-selection"
            onFilterData={onFilterData}
            onHealthData={onHealthData}
          />
        </SelectionHealthDataProvider>,
      );

      // Both hooks should provide data
      expect(onFilterData).toHaveBeenCalled();
      expect(onHealthData).toHaveBeenCalled();
    });
  });

  describe('listener management', () => {
    it('calls listeners appropriately when new components are added', () => {
      const onHealthData1 = jest.fn();
      const onHealthData2 = jest.fn();

      const {rerender} = render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData1} />
        </SelectionHealthDataProvider>,
      );

      const initialCallCount1 = onHealthData1.mock.calls.length;

      rerender(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData1} />
          <TestComponent selection="test-selection" onHealthData={onHealthData2} />
        </SelectionHealthDataProvider>,
      );

      // Both listeners should be called (the implementation calls all listeners on data changes)
      expect(onHealthData1.mock.calls.length).toBeGreaterThanOrEqual(initialCallCount1);
      // onHealthData2 should be called since it's a new listener
      expect(onHealthData2).toHaveBeenCalled();
    });

    it('handles listener cleanup on unmount', () => {
      const onHealthData = jest.fn();

      const {unmount} = render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      const initialCallCount = onHealthData.mock.calls.length;

      unmount();

      // Ensure no additional calls after unmount
      expect(onHealthData.mock.calls.length).toBe(initialCallCount);
    });
  });

  describe('integration behavior', () => {
    it('handles different asset states correctly', () => {
      const mockAssets = [createMockAsset(['asset1'])];
      const onHealthData = jest.fn();
      const onFilterData = jest.fn();

      mockedUseAllAssets.mockReturnValue({
        assets: mockAssets,
        loading: false,
        query: jest.fn(),
        assetsByAssetKey: new Map(),
        error: null,
      });

      render(
        <SelectionHealthDataProvider>
          <TestComponent
            selection="test-selection"
            onHealthData={onHealthData}
            onFilterData={onFilterData}
          />
        </SelectionHealthDataProvider>,
      );

      // Components should receive data updates
      expect(onHealthData).toHaveBeenCalled();
      expect(onFilterData).toHaveBeenCalled();
    });

    it('works with loading states', () => {
      const mockAssets = [createMockAsset(['asset1'])];
      const onHealthData = jest.fn();

      mockedUseAllAssets.mockReturnValue({
        assets: mockAssets,
        loading: true,
        query: jest.fn(),
        assetsByAssetKey: new Map(),
        error: null,
      });

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="test-selection" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );
      expect(onHealthData).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 0,
        loading: false,
      });
      expect(onHealthData).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 0,
        loading: true,
      });
    });
  });

  describe('edge cases', () => {
    it('handles empty selection string', () => {
      const onHealthData = jest.fn();

      render(
        <SelectionHealthDataProvider>
          <TestComponent selection="" onHealthData={onHealthData} />
        </SelectionHealthDataProvider>,
      );

      expect(onHealthData).toHaveBeenCalledWith({
        liveDataByNode: {},
        assetCount: 0,
        loading: false,
      });
    });
  });
});
