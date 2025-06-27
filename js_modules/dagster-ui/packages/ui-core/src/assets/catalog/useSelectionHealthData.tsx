import React, {useContext, useLayoutEffect, useMemo, useRef} from 'react';

import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {useAllAssets} from '../useAllAssets';

type SelectionHealthData = {
  liveDataByNode: Record<string, AssetHealthFragment>;
  assetCount: number;
  loading: boolean;
};

export const SelectionHealthDataContext = React.createContext<{
  watchSelection: (selection: string, setData: (data: SelectionHealthData) => void) => void;
}>({
  watchSelection: () => {},
});

const emptyListeners = new Set<(data: SelectionHealthData) => void>();

export const SelectionHealthDataProvider = ({children}: {children: React.ReactNode}) => {
  const [selections, setSelections] = React.useState<Set<string>>(() => new Set());
  const [dataListeners, setDataListeners] = React.useState<
    Record<string, Set<(data: SelectionHealthData) => void>>
  >({});

  const watchSelection = React.useCallback(
    (selection: string, setData: (data: SelectionHealthData) => void) => {
      setSelections((selections) => {
        const newSelections = new Set(selections);
        newSelections.add(selection);
        return newSelections;
      });

      setDataListeners((dataListeners) => {
        return {
          ...dataListeners,
          [selection]: new Set([...(dataListeners[selection] || []), setData]),
        };
      });

      return () => {
        setDataListeners((dataListeners) => {
          const copy = new Set(dataListeners[selection] || []);
          copy.delete(setData);
          return {
            ...dataListeners,
            [selection]: copy,
          };
        });
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
          dataListeners={dataListeners[selection] || emptyListeners}
        />
      ))}
      {children}
    </SelectionHealthDataContext.Provider>
  );
};

const SelectionHealthDataObserver = React.memo(
  ({
    selection,
    dataListeners,
  }: {
    selection: string;
    dataListeners: Set<(data: SelectionHealthData) => void>;
  }) => {
    const skip = !dataListeners.size;
    const {assets, loading} = useAllAssets();
    const {filtered} = useAssetSelectionFiltering({
      assets,
      assetSelection: selection,
      loading,
      useWorker: false,
      includeExternalAssets: true,
      skip,
    });

    const {liveDataByNode} = useAssetsHealthData(
      useMemo(() => filtered.map((asset) => asset.key), [filtered]),
      getSelectionThreadId(selection),
      skip,
    );

    const previousListeners = useRef<Set<(data: SelectionHealthData) => void>>(dataListeners);
    const newListeners = useMemo(() => {
      const newListeners = new Set<(data: SelectionHealthData) => void>();
      dataListeners.forEach((listener) => {
        if (!previousListeners.current.has(listener)) {
          newListeners.add(listener);
        }
      });
      return newListeners;
    }, [dataListeners, previousListeners]);
    previousListeners.current = dataListeners;

    const isLoading = loading || filtered.length !== Object.keys(liveDataByNode).length;

    const data: SelectionHealthData = useMemo(
      () => ({
        liveDataByNode,
        assetCount: filtered.length,
        loading: isLoading,
      }),
      [liveDataByNode, filtered.length, isLoading],
    );

    useLayoutEffect(() => {
      dataListeners.forEach((listener) => {
        if (newListeners.has(listener)) {
          // Don't notify listeners that are new because they will be notified by the next effect
          return;
        }
        listener(data);
      });
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [data]);

    useLayoutEffect(() => {
      newListeners.forEach((listener) => listener(data));
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [newListeners]);

    return <></>;
  },
);

export const useSelectionHealthData = (selection: string) => {
  const {watchSelection} = useContext(SelectionHealthDataContext);

  const [data, setData] = React.useState<SelectionHealthData>(() => ({
    liveDataByNode: {},
    assetCount: 0,
    loading: false,
  }));

  useLayoutEffect(() => {
    return watchSelection(selection, setData);
  }, [selection, watchSelection]);

  return data;
};

function getSelectionThreadId(selection: string) {
  return `selection-${selection}`;
}
