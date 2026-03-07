import React, {useContext, useLayoutEffect, useMemo, useReducer} from 'react';

import {AssetHealthData, useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {useUpdatingRef} from '../../hooks/useUpdatingRef';
import {DeferredCallbackRegistry} from '../../util/DeferredCallbackRegistry';
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
  }) => () => void;
}>({
  watchSelection: () => () => {},
});

export const SelectionHealthDataProvider = ({children}: {children: React.ReactNode}) => {
  const [selections, setSelections] = React.useState<Set<string>>(() => new Set());

  /**
   * Whenever new listeners are added to a registry, we need to force a re-render of the SelectionHealthDataObserver
   * so that it picks up the listeners from the registry and uses that information to determine whether
   * to fetch health data or calculate filter data.
   * We do this instead of using state to avoid needing to manage references and create new objects.
   */
  const [, forceRerender] = useReducer((s: number) => s + 1, 0);

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
      const registry = getSelectionRegistry(selection, registries);
      const unwatch = registry.watchSelection(setHealthData, setFilterData);
      forceRerender();
      return () => {
        unwatch();
        forceRerender();
      };
    },
    [registries],
  );

  return (
    <SelectionHealthDataContext.Provider value={{watchSelection}}>
      {Array.from(selections).map((selection) => {
        const registry = getSelectionRegistry(selection, registries);
        return (
          <SelectionHealthDataObserver
            key={selection}
            selection={selection}
            registry={registry}
            filterListeners={registry.getFilterListeners()}
            healthListeners={registry.getHealthListeners()}
          />
        );
      })}
      {children}
    </SelectionHealthDataContext.Provider>
  );
};

const SelectionHealthDataObserver = React.memo(
  ({
    selection,
    registry,
    filterListeners,
    healthListeners,
  }: {
    selection: string;
    registry: SelectionRegistry;
    filterListeners: Set<(data: SelectionFilterData) => void>;
    healthListeners: Set<(data: SelectionHealthData) => void>;
  }) => {
    const skipFilters = !filterListeners.size && !healthListeners.size;
    const skipHealth = !healthListeners.size;

    const {assets, loading} = useAllAssets();

    const {filtered, loading: filterLoading} = useAssetSelectionFiltering<(typeof assets)[number]>({
      assets,
      assetSelection: selection,
      loading,
      includeExternalAssets: true,
      skip: skipFilters,
    });

    const {liveDataByNode} = useAssetsHealthData({
      assetKeys: useMemo(() => filtered.map((asset) => asset.key), [filtered]),
      thread: getSelectionThreadId(selection),
      skip: skipHealth,
      loading: filterLoading || skipFilters,
    });

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

    const hasHealthListeners = healthListeners.size;
    useLayoutEffect(() => {
      if (!hasHealthListeners) {
        AssetHealthData.manager.pauseThread(getSelectionThreadId(selection));
      } else {
        AssetHealthData.manager.unpauseThread(getSelectionThreadId(selection));
      }
    }, [hasHealthListeners, selection]);

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

export const useSelectionFilterData = ({selection, skip}: {selection: string; skip?: boolean}) => {
  const {watchSelection} = useContext(SelectionHealthDataContext);

  const [filterData, setFilterData] = React.useState<SelectionFilterData>(() => ({
    assets: [],
    loading: false,
  }));

  useLayoutEffect(() => {
    if (skip) {
      return;
    }
    return watchSelection({selection, setFilterData});
  }, [selection, watchSelection, skip]);
  return filterData;
};

function getSelectionThreadId(selection: string) {
  return `selection-${selection}`;
}

type OnWatchSelection = (
  setHealthData?: (data: SelectionHealthData) => void,
  setFilterData?: (data: SelectionFilterData) => void,
) => void;

type SelectionCallbacks = {
  setHealthData?: (data: SelectionHealthData) => void;
  setFilterData?: (data: SelectionFilterData) => void;
};

export class SelectionRegistry {
  private registry = new DeferredCallbackRegistry<SelectionCallbacks>();

  public registerOnWatchSelection(fn: OnWatchSelection) {
    this.registry.register(({setHealthData, setFilterData}) => {
      fn(setHealthData, setFilterData);
    });
  }

  public watchSelection(
    setHealthData?: (data: SelectionHealthData) => void,
    setFilterData?: (data: SelectionFilterData) => void,
  ) {
    return this.registry.watch({setHealthData, setFilterData});
  }

  public getFilterListeners() {
    return this.registry.getListeners('setFilterData');
  }

  public getHealthListeners() {
    return this.registry.getListeners('setHealthData');
  }
}

function getSelectionRegistry(
  selection: string,
  registries: Record<string, SelectionRegistry>,
): SelectionRegistry {
  if (!registries[selection]) {
    registries[selection] = new SelectionRegistry();
  }
  return registries[selection];
}
