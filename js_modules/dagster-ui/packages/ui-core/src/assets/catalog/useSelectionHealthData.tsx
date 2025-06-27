import React, {useContext, useLayoutEffect, useMemo} from 'react';

import {useAssetsHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetHealthFragment} from '../../asset-data/types/AssetHealthDataProvider.types';
import {useAssetSelectionFiltering} from '../../asset-selection/useAssetSelectionFiltering';
import {useAllAssets} from '../useAllAssets';

export const SelectionHealthDataContext = React.createContext<{
  watchSelection: (
    selection: string,
    setHealthData: (healthData: Record<string, AssetHealthFragment>) => void,
    setAssetCount: (assetCount: number) => void,
    setLoading: (loading: boolean) => void,
  ) => void;
}>({
  watchSelection: () => {},
});

const emptyListeners = new Set<(...params: any[]) => void>();

export const SelectionHealthDataProvider = ({children}: {children: React.ReactNode}) => {
  const [selections, setSelections] = React.useState<Set<string>>(() => new Set());
  const [liveDataByNodeListeners, setLiveDataByNodeListeners] = React.useState<
    Record<string, Set<(healthData: Record<string, AssetHealthFragment>) => void>>
  >({});
  const [assetCountListeners, setAssetCountListeners] = React.useState<
    Record<string, Set<(assetCount: number) => void>>
  >({});
  const [loadingListeners, setLoadingListeners] = React.useState<
    Record<string, Set<(loading: boolean) => void>>
  >({});

  const watchSelection = React.useCallback(
    (
      selection: string,
      setHealthData: (healthData: Record<string, AssetHealthFragment>) => void,
      setAssetCount: (assetCount: number) => void,
      setLoading: (loading: boolean) => void,
    ) => {
      setSelections((selections) => {
        selections.add(selection);
        return selections;
      });

      setLiveDataByNodeListeners((liveDataByNodeListeners) => {
        return {
          ...liveDataByNodeListeners,
          [selection]: new Set([...(liveDataByNodeListeners[selection] || []), setHealthData]),
        };
      });

      setLoadingListeners((loadingListeners) => {
        return {
          ...loadingListeners,
          [selection]: new Set([...(loadingListeners[selection] || []), setLoading]),
        };
      });

      setAssetCountListeners((assetCountListeners) => {
        return {
          ...assetCountListeners,
          [selection]: new Set([...(assetCountListeners[selection] || []), setAssetCount]),
        };
      });

      return () => {
        setLiveDataByNodeListeners((liveDataByNodeListeners) => {
          const newListeners = {...liveDataByNodeListeners};
          newListeners[selection]?.delete(setHealthData);
          return newListeners;
        });

        setAssetCountListeners((assetCountListeners) => {
          const newListeners = {...assetCountListeners};
          newListeners[selection]?.delete(setAssetCount);
          return newListeners;
        });

        setLoadingListeners((loadingListeners) => {
          const newListeners = {...loadingListeners};
          newListeners[selection]?.delete(setLoading);
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
          liveDataByNodeListeners={liveDataByNodeListeners[selection] || emptyListeners}
          assetCountListeners={assetCountListeners[selection] || emptyListeners}
          loadingListeners={loadingListeners[selection] || emptyListeners}
        />
      ))}
      {children}
    </SelectionHealthDataContext.Provider>
  );
};

const SelectionHealthDataObserver = React.memo(
  ({
    selection,
    liveDataByNodeListeners,
    assetCountListeners,
    loadingListeners,
  }: {
    selection: string;
    liveDataByNodeListeners: Set<(healthData: Record<string, AssetHealthFragment>) => void>;
    assetCountListeners: Set<(assetCount: number) => void>;
    loadingListeners: Set<(loading: boolean) => void>;
  }) => {
    const skip = !liveDataByNodeListeners.size;
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

    useLayoutEffect(() => {
      if (liveDataByNodeListeners) {
        liveDataByNodeListeners.forEach((listener) => listener(liveDataByNode));
      }
    }, [liveDataByNodeListeners, liveDataByNode]);

    useLayoutEffect(() => {
      if (assetCountListeners) {
        assetCountListeners.forEach((listener) => listener(filtered.length));
      }
    }, [assetCountListeners, filtered.length]);

    const isLoading = loading || filtered.length !== Object.keys(liveDataByNode).length;

    useLayoutEffect(() => {
      loadingListeners.forEach((listener) => listener(isLoading));
    }, [loadingListeners, isLoading]);

    return <></>;
  },
);

export const useSelectionHealthData = (selection: string) => {
  const {watchSelection} = useContext(SelectionHealthDataContext);

  const [liveDataByNode, setLiveDataByNode] = React.useState<Record<string, AssetHealthFragment>>(
    () => ({}),
  );
  const [assetCount, setAssetCount] = React.useState(0);
  const [loading, setLoading] = React.useState(false);

  useLayoutEffect(
    () => watchSelection(selection, setLiveDataByNode, setAssetCount, setLoading),
    [selection, watchSelection],
  );

  return {liveDataByNode, loading, assetCount};
};

function getSelectionThreadId(selection: string) {
  return `selection-${selection}`;
}
