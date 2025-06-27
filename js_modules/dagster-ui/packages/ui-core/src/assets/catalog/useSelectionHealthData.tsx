import React, {useContext, useLayoutEffect, useMemo} from 'react';

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
        selections.add(selection);
        return selections;
      });

      setDataListeners((dataListeners) => {
        return {
          ...dataListeners,
          [selection]: new Set([...(dataListeners[selection] || []), setData]),
        };
      });

      return () => {
        setDataListeners((dataListeners) => {
          const newListeners = {...dataListeners};
          newListeners[selection]?.delete(setData);
          return newListeners;
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

    const isLoading = loading || filtered.length !== Object.keys(liveDataByNode).length;

    useLayoutEffect(() => {
      const data: SelectionHealthData = {
        liveDataByNode,
        assetCount: filtered.length,
        loading: isLoading,
      };

      dataListeners.forEach((listener) => listener(data));
    }, [dataListeners, liveDataByNode, filtered.length, isLoading]);

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
