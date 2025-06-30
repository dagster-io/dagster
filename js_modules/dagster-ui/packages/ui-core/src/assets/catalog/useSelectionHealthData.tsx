import React, {useContext, useLayoutEffect, useMemo, useReducer} from 'react';

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
      if (!registries[selection]) {
        registries[selection] = new SelectionRegistry();
      }
      const registry = registries[selection]!;
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
      {Array.from(selections).map((selection) => (
        <SelectionHealthDataObserver
          key={selection}
          selection={selection}
          registry={registries[selection]!}
          filterListeners={registries[selection]!.getFilterListeners()}
          healthListeners={registries[selection]!.getHealthListeners()}
        />
      ))}
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
      useWorker: false,
      includeExternalAssets: true,
      skip: skipFilters,
    });

    const {liveDataByNode} = useAssetsHealthData({
      assetKeys: useMemo(() => filtered.map((asset) => asset.key), [filtered]),
      thread: getSelectionThreadId(selection),
      skip: skipHealth,
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
    _setHealthData?: (data: SelectionHealthData) => void,
    _setFilterData?: (data: SelectionFilterData) => void,
  ) {
    // Wrap the callbacks to make unique references in case callers are doing
    // weird shit like using the same callbacks multiple times.
    const setHealthData = _setHealthData
      ? (data: SelectionHealthData) => {
          _setHealthData?.(data);
        }
      : undefined;
    const setFilterData = _setFilterData
      ? (data: SelectionFilterData) => {
          _setFilterData?.(data);
        }
      : undefined;
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

    return () => {
      if (setFilterData) {
        this.filterListeners.delete(setFilterData);
      }
      if (setHealthData) {
        this.healthListeners.delete(setHealthData);
      }
    };
  }

  public getFilterListeners() {
    return this.filterListeners;
  }

  public getHealthListeners() {
    return this.healthListeners;
  }
}
