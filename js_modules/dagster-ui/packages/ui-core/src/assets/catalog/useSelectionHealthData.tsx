import React, {useContext, useLayoutEffect, useMemo} from 'react';

import {AssetHealthData, useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {useAllAssets} from '../useAllAssets';

type SelectionHealthData = {
  liveDataByNode: Record<string, AssetHealthFragment>;
  assetCount: number;
  loading: boolean;
};

type SelectionFilterData = {
  assets: ReturnType<typeof useAllAssets>['assets'];
  loading: boolean;
};

export const SelectionHealthDataContext = React.createContext<{
  watchSelection: (params: {
    selection: string;
    setHealthData?: (data: SelectionHealthData) => void;
    setFilterData?: (data: SelectionFilterData) => void;
  }) => void;
}>({
  watchSelection: () => {},
});

export const SelectionHealthDataProvider = ({children}: {children: React.ReactNode}) => {
  const [selections, setSelections] = React.useState<Set<string>>(() => new Set());

  const registries: Record<string, SelectionRegistry> = useMemo(() => ({}), []);

  const watchSelection = React.useCallback(
    ({
      selection,
      setHealthData,
      setFilterData,
    }: {
      selection: string;
      setHealthData?: (data: SelectionHealthData) => void;
      setFilterData?: (data: SelectionFilterData) => void;
    }) => {
      setSelections((selections) => {
        const newSelections = new Set(selections);
        newSelections.add(selection);
        return newSelections;
      });
      if (!registries[selection]) {
        registries[selection] = new SelectionRegistry();
      }
      const registry = registries[selection]!;
      registry.watchSelection(setHealthData, setFilterData);
    },
    [registries],
  );

  return (
    <SelectionHealthDataContext.Provider value={{watchSelection}}>
      {Array.from(selections).map((selection) => (
        <SelectionHealthDataObserver
          key={selection}
          selection={selection}
          registry={registries[selection]!}
        />
      ))}
      {children}
    </SelectionHealthDataContext.Provider>
  );
};

const SelectionHealthDataObserver = React.memo(
  ({selection, registry}: {selection: string; registry: SelectionRegistry}) => {
    const filterListeners = registry.getFilterListeners();
    const healthListeners = registry.getHealthListeners();

    const skipFilters = !filterListeners.size && !healthListeners.size;
    const skipHealth = !healthListeners.size;

    const {assets, loading} = useAllAssets();
    const {filtered, loading: filterLoading} = useAssetSelectionFiltering<(typeof assets)[number]>({
      assets,
      assetSelection: selection,
      loading,
      useWorker: false,
      includeExternalAssets: true,
      skip: skipFilters,
    });

    const {liveDataByNode} = useAssetsHealthData(
      useMemo(() => filtered.map((asset) => asset.key), [filtered]),
      getSelectionThreadId(selection),
      skipHealth,
    );

    const isLoading = loading || filtered.length !== Object.keys(liveDataByNode).length;

    const healthData: SelectionHealthData = useMemo(
      () => ({
        liveDataByNode,
        assetCount: filtered.length,
        loading: isLoading,
      }),
      [liveDataByNode, filtered.length, isLoading],
    );

    const filterData: SelectionFilterData = useMemo(
      () => ({assets: filtered, loading: filterLoading}),
      [filtered, filterLoading],
    );

    const dataRef = useUpdatingRef({filterData, healthData});

    useLayoutEffect(() => {
      registry.registerOnWatchSelection((setHealthData, setFilterData) => {
        setHealthData?.(dataRef.current.healthData);
        setFilterData?.(dataRef.current.filterData);
      });
    }, [registry, dataRef]);

    useLayoutEffect(() => {
      registry.getFilterListeners().forEach((listener) => listener(filterData));
    }, [filterData, registry]);
    useLayoutEffect(() => {
      registry.getHealthListeners().forEach((listener) => listener(healthData));
    }, [healthData, registry]);

    useLayoutEffect(() => {
      if (!healthListeners.size) {
        AssetHealthData.manager.pauseThread(getSelectionThreadId(selection));
      } else {
        AssetHealthData.manager.unpauseThread(getSelectionThreadId(selection));
      }
    }, [healthListeners, selection]);

    return <></>;
  },
);

export const useSelectionHealthData = ({selection}: {selection: string}) => {
  const {watchSelection} = useContext(SelectionHealthDataContext);

  const [healthData, setHealthData] = React.useState<SelectionHealthData>(() => ({
    liveDataByNode: {},
    assetCount: 0,
    loading: false,
  }));

  useLayoutEffect(() => {
    return watchSelection({selection, setHealthData});
  }, [selection, watchSelection]);

  return healthData;
};

export const useSelectionFilterData = ({selection}: {selection: string}) => {
  const {watchSelection} = useContext(SelectionHealthDataContext);

  const [filterData, setFilterData] = React.useState<SelectionFilterData>(() => ({
    assets: [],
    loading: false,
  }));

  useLayoutEffect(() => {
    return watchSelection({selection, setFilterData});
  }, [selection, watchSelection]);
  return filterData;
};

function getSelectionThreadId(selection: string) {
  return `selection-${selection}`;
}

type OnWatchSelection = (
  setHealthData?: (data: SelectionHealthData) => void,
  setFilterData?: (data: SelectionFilterData) => void,
) => void;

export class SelectionRegistry {
  private queue: Array<{
    setHealthData?: (data: SelectionHealthData) => void;
    setFilterData?: (data: SelectionFilterData) => void;
  }> = [];

  private filterListeners = new Set<(data: SelectionFilterData) => void>();
  private healthListeners = new Set<(data: SelectionHealthData) => void>();

  private _onWatchSelection: OnWatchSelection | null = null;

  public registerOnWatchSelection(fn: OnWatchSelection) {
    this._onWatchSelection = fn;
    while (this.queue.length) {
      const {setHealthData, setFilterData} = this.queue.shift()!;
      fn(setHealthData, setFilterData);
    }
  }

  public watchSelection(
    setHealthData?: (data: SelectionHealthData) => void,
    setFilterData?: (data: SelectionFilterData) => void,
  ) {
    if (setFilterData) {
      this.filterListeners.add(setFilterData);
    }
    if (setHealthData) {
      this.healthListeners.add(setHealthData);
    }
    if (this._onWatchSelection) {
      this._onWatchSelection(setHealthData, setFilterData);
    } else {
      this.queue.push({setHealthData, setFilterData});
    }
  }

  public getFilterListeners() {
    return this.filterListeners;
  }

  public getHealthListeners() {
    return this.healthListeners;
  }
}
