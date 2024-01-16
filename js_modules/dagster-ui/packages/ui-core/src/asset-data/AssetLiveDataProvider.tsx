import {useApolloClient} from '@apollo/client';
import uniq from 'lodash/uniq';
import React from 'react';

import {observeAssetEventsInRuns} from '../asset-graph/AssetRunLogObserver';
import {LiveDataForNode, tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {useDocumentVisibility} from '../hooks/useDocumentVisibility';
import {useDidLaunchEvent} from '../runs/RunUtils';

import {AssetDataRefreshButton} from './AssetDataRefreshButton';
import {AssetLiveDataThreadID} from './AssetLiveDataThread';
import {AssetLiveDataThreadManager} from './AssetLiveDataThreadManager';
import {SUBSCRIPTION_IDLE_POLL_RATE, SUBSCRIPTION_MAX_POLL_RATE} from './util';

export const LiveDataPollRateContext = React.createContext<number>(SUBSCRIPTION_IDLE_POLL_RATE);

export const AssetLiveDataRefreshContext = React.createContext<{
  isGloballyRefreshing: boolean;
  oldestDataTimestamp: number;
  refresh: () => void;
}>({
  isGloballyRefreshing: false,
  oldestDataTimestamp: Infinity,
  refresh: () => {},
});

export function useAssetLiveData(
  assetKey: AssetKeyInput,
  thread: AssetLiveDataThreadID = 'default',
) {
  const {liveDataByNode, refresh, refreshing} = useAssetsLiveData(
    React.useMemo(() => [assetKey], [assetKey]),
    thread,
  );
  return {
    liveData: liveDataByNode[tokenForAssetKey(assetKey)],
    refresh,
    refreshing,
  };
}

export function useAssetsLiveData(
  assetKeys: AssetKeyInput[],
  thread: AssetLiveDataThreadID = 'default',
) {
  const [data, setData] = React.useState<Record<string, LiveDataForNode>>({});
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  const client = useApolloClient();
  const manager = AssetLiveDataThreadManager.getInstance(client);

  React.useEffect(() => {
    const setDataSingle = (stringKey: string, assetData?: LiveDataForNode) => {
      setData((data) => {
        const copy = {...data};
        if (!assetData) {
          delete copy[stringKey];
        } else {
          copy[stringKey] = assetData;
        }
        return copy;
      });
    };
    const unsubscribeCallbacks = assetKeys.map((key) =>
      manager.subscribe(key, setDataSingle, thread),
    );
    return () => {
      unsubscribeCallbacks.forEach((cb) => {
        cb();
      });
    };
  }, [assetKeys, manager, thread]);

  return {
    liveDataByNode: data,

    refresh: React.useCallback(() => {
      manager.refreshKeys(assetKeys);
      setIsRefreshing(true);
    }, [assetKeys, manager]),

    refreshing: React.useMemo(() => {
      if (isRefreshing && !manager.areKeysRefreshing(assetKeys)) {
        setTimeout(() => {
          setIsRefreshing(false);
        });
        return false;
      }
      return true;
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [assetKeys, data, isRefreshing]),
  };
}

export const AssetLiveDataProvider = ({children}: {children: React.ReactNode}) => {
  const [allObservedKeys, setAllObservedKeys] = React.useState<AssetKeyInput[]>([]);

  const client = useApolloClient();
  const manager = AssetLiveDataThreadManager.getInstance(client);

  const [isGloballyRefreshing, setIsGloballyRefreshing] = React.useState(false);
  const [oldestDataTimestamp, setOldestDataTimestamp] = React.useState(0);

  const onUpdatingOrUpdated = React.useCallback(() => {
    const {isRefreshing, oldestDataTimestamp} = manager.getOldestDataTimestamp();
    setIsGloballyRefreshing(isRefreshing);
    setOldestDataTimestamp(oldestDataTimestamp);
  }, [manager]);

  React.useEffect(() => {
    manager.setOnSubscriptionsChangedCallback((keys) =>
      setAllObservedKeys(keys.map((key) => ({path: key.split('/')}))),
    );
    manager.setOnUpdatingOrUpdated(onUpdatingOrUpdated);
  }, [manager, onUpdatingOrUpdated]);

  const isDocumentVisible = useDocumentVisibility();

  const pollRate = React.useContext(LiveDataPollRateContext);

  React.useEffect(() => {
    manager.onDocumentVisiblityChange(isDocumentVisible);
  }, [manager, isDocumentVisible]);

  React.useEffect(() => {
    manager.setPollRate(pollRate);
  }, [manager, pollRate]);

  useDidLaunchEvent(() => {
    manager.refreshKeys();
  }, SUBSCRIPTION_MAX_POLL_RATE);

  React.useEffect(() => {
    const assetKeyTokens = new Set(allObservedKeys.map(tokenForAssetKey));
    const dataForObservedKeys = allObservedKeys
      .map((key) => manager.getCacheEntry(key))
      .filter((n) => n) as LiveDataForNode[];

    const assetStepKeys = new Set(dataForObservedKeys.flatMap((n) => n.opNames));

    const runInProgressId = uniq(
      dataForObservedKeys.flatMap((p) => [
        ...p.unstartedRunIds,
        ...p.inProgressRunIds,
        ...p.assetChecks
          .map((c) => c.executionForLatestMaterialization)
          .filter(Boolean)
          .map((e) => e!.runId),
      ]),
    ).sort();

    const unobserve = observeAssetEventsInRuns(runInProgressId, (events) => {
      if (
        events.some(
          (e) =>
            (e.assetKey && assetKeyTokens.has(tokenForAssetKey(e.assetKey))) ||
            (e.stepKey && assetStepKeys.has(e.stepKey)),
        )
      ) {
        manager.refreshKeys();
      }
    });
    return unobserve;
  }, [allObservedKeys, manager]);

  return (
    <AssetLiveDataRefreshContext.Provider
      value={{
        isGloballyRefreshing,
        oldestDataTimestamp,
        refresh: React.useCallback(() => {
          manager.refreshKeys();
        }, [manager]),
      }}
    >
      {children}
    </AssetLiveDataRefreshContext.Provider>
  );
};

export function AssetLiveDataRefresh() {
  const {isGloballyRefreshing, oldestDataTimestamp, refresh} = React.useContext(
    AssetLiveDataRefreshContext,
  );
  return (
    <AssetDataRefreshButton
      isRefreshing={isGloballyRefreshing}
      oldestDataTimestamp={oldestDataTimestamp}
      onRefresh={refresh}
    />
  );
}
