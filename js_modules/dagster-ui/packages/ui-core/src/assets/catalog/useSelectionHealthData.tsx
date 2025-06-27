import React, {useContext, useLayoutEffect, useMemo, useRef} from 'react';

import {AssetHealthData, useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {useAllAssets} from '../useAllAssets';

type SelectionHealthData = {
  liveDataByNode: Record<string, AssetHealthFragment>;
  assetCount: number;
  loading: boolean;
};

type SelectionFilterData = {
  assets: AssetFragment[];
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

const emptyListeners = new Set<(data: any) => void>();

export const SelectionHealthDataProvider = ({children}: {children: React.ReactNode}) => {
  const [selections, setSelections] = React.useState<Set<string>>(() => new Set());
  const [filterListeners, setFilterListeners] = React.useState<
    Record<string, Set<(data: SelectionFilterData) => void>>
  >({});
  const [healthListeners, setHealthListeners] = React.useState<
    Record<string, Set<(data: SelectionHealthData) => void>>
  >({});

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

      if (setFilterData) {
        setFilterListeners((filterListeners) => {
          const copy = new Set(filterListeners[selection] || []);
          copy.add(setFilterData);
          return {
            ...filterListeners,
            [selection]: copy,
          };
        });
      }

      if (setHealthData) {
        setHealthListeners((healthListeners) => {
          const copy = new Set(healthListeners[selection] || []);
          copy.add(setHealthData);
          return {
            ...healthListeners,
            [selection]: copy,
          };
        });
      }

      return () => {
        if (setFilterData) {
          setFilterListeners((filterListeners) => {
            const copy = new Set(filterListeners[selection] || []);
            copy.delete(setFilterData);
            return {
              ...filterListeners,
              [selection]: copy,
            };
          });
        }
        if (setHealthData) {
          setHealthListeners((healthListeners) => {
            const copy = new Set(healthListeners[selection] || []);
            copy.delete(setHealthData);
            return {
              ...healthListeners,
              [selection]: copy,
            };
          });
        }
      };
    },
    [],
  );

  return (
    <SelectionHealthDataContext.Provider value={{watchSelection}}>
      {Array.from(selections).map((selection) => (
        <SelectionHealthDataObserver
          key={selection}
          selection={selection}
          filterListeners={filterListeners[selection] || emptyListeners}
          healthListeners={healthListeners[selection] || emptyListeners}
        />
      ))}
      {children}
    </SelectionHealthDataContext.Provider>
  );
};

const SelectionHealthDataObserver = React.memo(
  ({
    selection,
    filterListeners,
    healthListeners,
  }: {
    selection: string;

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

    const {liveDataByNode} = useAssetsHealthData(
      useMemo(() => filtered.map((asset) => asset.key), [filtered]),
      getSelectionThreadId(selection),
      skipHealth,
    );

    const previousFilterListenersRef =
      useRef<Set<(data: SelectionFilterData) => void>>(filterListeners);
    const previousHealthListenersRef =
      useRef<Set<(data: SelectionHealthData) => void>>(healthListeners);

    const previousListeners = previousFilterListenersRef.current;
    const newFilterListeners = useMemo(
      () => getNewListeners(filterListeners, previousListeners),
      [filterListeners, previousListeners],
    );
    const previousHealthListeners = previousHealthListenersRef.current;
    const newHealthListeners = useMemo(
      () => getNewListeners(healthListeners, previousHealthListeners),
      [healthListeners, previousHealthListeners],
    );

    previousFilterListenersRef.current = filterListeners;
    previousHealthListenersRef.current = healthListeners;

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

    useLayoutEffect(() => {
      newHealthListeners.forEach((listener) => {
        if (healthListeners.has(listener)) {
          // Don't notify listeners that are new because they will be notified by the next effect
          return;
        }
        listener(healthData);
      });
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [healthData]);

    useLayoutEffect(() => {
      newHealthListeners.forEach((listener) => listener(healthData));
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [newHealthListeners, healthData]);

    useLayoutEffect(() => {
      newFilterListeners.forEach((listener) => {
        if (filterListeners.has(listener)) {
          // Don't notify listeners that are new because they will be notified by the next effect
          return;
        }
        listener(filterData);
      });
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filterData]);

    useLayoutEffect(() => {
      newFilterListeners.forEach((listener) => listener(filterData));
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [newFilterListeners, filterData]);

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

function getNewListeners<T>(listeners: Set<T>, previousListeners: Set<T>) {
  const newListeners = new Set<T>();
  listeners.forEach((listener) => {
    if (!previousListeners.has(listener)) {
      newListeners.add(listener);
    }
  });
  return newListeners;
}
