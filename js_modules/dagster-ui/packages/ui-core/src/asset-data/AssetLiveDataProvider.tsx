import uniq from 'lodash/uniq';
import React, {useCallback, useMemo, useReducer, useRef} from 'react';

import {AssetBaseData, __resetForJest as __resetBaseData} from './AssetBaseDataProvider';
import {AssetHealthData, __resetForJest as __resetHealthData} from './AssetHealthDataProvider';
import {
  AssetStaleStatusData,
  __resetForJest as __resetStaleData,
} from './AssetStaleStatusDataProvider';
import {observeAssetEventsInRuns} from '../asset-graph/AssetRunLogObserver';
import {LiveDataForNodeWithStaleData, tokenForAssetKey} from '../asset-graph/Utils';
import {AssetKeyInput} from '../graphql/types';
import {useThrottledEffect} from '../hooks/useThrottledEffect';
import {LiveDataPollRateContext} from '../live-data-provider/LiveDataProvider';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';
import {SUBSCRIPTION_MAX_POLL_RATE} from '../live-data-provider/util';
import {useDidLaunchEvent} from '../runs/RunUtils';

export function useAssetLiveData(assetKey: AssetKeyInput, thread: LiveDataThreadID = 'default') {
  const key = tokenForAssetKey(assetKey);
  const {
    liveData: staleData,
    refresh: refreshStaleData,
    refreshing: staleDataRefreshing,
  } = AssetStaleStatusData.useLiveDataSingle(key, thread);
  const {
    liveData: baseData,
    refresh: refreshBaseData,
    refreshing: baseDataRefreshing,
  } = AssetBaseData.useLiveDataSingle(key, thread);

  const refresh = useCallback(() => {
    refreshBaseData();
    refreshStaleData();
  }, [refreshBaseData, refreshStaleData]);
  const refreshing = baseDataRefreshing || staleDataRefreshing;

  if (baseData && staleData) {
    return {
      liveData: {
        ...staleData,
        ...baseData,
      },
      refresh,
      refreshing,
    };
  }
  return {liveData: undefined, refresh, refreshing};
}

export function useAssetsLiveData(
  assetKeys: AssetKeyInput[],
  thread: LiveDataThreadID = 'default',
) {
  const keys = React.useMemo(() => assetKeys.map((key) => tokenForAssetKey(key)), [assetKeys]);
  const {
    liveDataByNode: staleDataByNode,
    refresh: refreshStaleData,
    refreshing: staleDataRefreshing,
  } = AssetStaleStatusData.useLiveData(keys, thread);
  const {
    liveDataByNode: baseDataByNode,
    refresh: refreshBaseData,
    refreshing: baseDataRefreshing,
  } = AssetBaseData.useLiveData(keys, thread);
  const completeDataByNode = useMemo(() => {
    const data: Record<string, LiveDataForNodeWithStaleData> = {};
    Object.keys(baseDataByNode).forEach((key) => {
      const baseData = baseDataByNode[key];
      const staleData = staleDataByNode[key];
      if (staleData && baseData) {
        data[key] = {...staleData, ...baseData};
      }
    });
    return data;
  }, [baseDataByNode, staleDataByNode]);
  const refresh = useCallback(() => {
    refreshBaseData();
    refreshStaleData();
  }, [refreshBaseData, refreshStaleData]);
  const refreshing = baseDataRefreshing || staleDataRefreshing;

  return {
    liveDataByNode: completeDataByNode,
    refresh,
    refreshing,
  };
}

export const AssetLiveDataProvider = ({children}: {children: React.ReactNode}) => {
  const [keysChanged, updateKeysChanged] = useReducer((s) => s + 1, 0);

  const staleKeysObserved = useRef<Set<string>[]>([]);
  const baseKeysObserved = useRef<Set<string>[]>([]);
  const healthKeysObserved = useRef<Set<string>[]>([]);

  React.useEffect(() => {
    AssetStaleStatusData.manager.setOnSubscriptionsChangedCallback((keys) => {
      staleKeysObserved.current = keys;
      updateKeysChanged();
    });
    AssetBaseData.manager.setOnSubscriptionsChangedCallback((keys) => {
      baseKeysObserved.current = keys;
      updateKeysChanged();
    });
    AssetHealthData.manager.setOnSubscriptionsChangedCallback((keys) => {
      healthKeysObserved.current = keys;
      updateKeysChanged();
    });
  }, []);

  const pollRate = React.useContext(LiveDataPollRateContext);

  React.useEffect(() => {
    AssetStaleStatusData.manager.setPollRate(pollRate);
    AssetBaseData.manager.setPollRate(pollRate);
    AssetHealthData.manager.setPollRate(pollRate);
  }, [pollRate]);

  useDidLaunchEvent(() => {
    AssetStaleStatusData.manager.invalidateCache();
    AssetBaseData.manager.invalidateCache();
    AssetHealthData.manager.invalidateCache();
  }, SUBSCRIPTION_MAX_POLL_RATE);

  useThrottledEffect(
    () => {
      const assetKeyTokensArray = [
        ...staleKeysObserved.current.flatMap((keySet) => Array.from(keySet)),
        ...baseKeysObserved.current.flatMap((keySet) => Array.from(keySet)),
        ...healthKeysObserved.current.flatMap((keySet) => Array.from(keySet)),
      ];
      const assetKeyTokens = new Set(assetKeyTokensArray);
      const dataForObservedKeys = assetKeyTokensArray
        .map((key) => AssetBaseData.manager.getCacheEntry(key)!)
        .filter((n) => n);

      const assetStepKeys = new Set(dataForObservedKeys.flatMap((n) => n.opNames));

      const runInProgressId = uniq(
        dataForObservedKeys.flatMap((p) => [...p.unstartedRunIds, ...p.inProgressRunIds]),
      ).sort();

      const unobserve = observeAssetEventsInRuns(runInProgressId, (events) => {
        if (
          events.some(
            (e) =>
              (e.assetKey && assetKeyTokens.has(tokenForAssetKey(e.assetKey))) ||
              (e.stepKey && assetStepKeys.has(e.stepKey)),
          )
        ) {
          AssetBaseData.manager.invalidateCache();
          AssetStaleStatusData.manager.invalidateCache();
          AssetHealthData.manager.invalidateCache();
        }
      });
      return unobserve;
    },
    [keysChanged],
    2000,
  );

  return (
    <AssetHealthData.LiveDataProvider>
      <AssetBaseData.LiveDataProvider>
        <AssetStaleStatusData.LiveDataProvider>{children}</AssetStaleStatusData.LiveDataProvider>
      </AssetBaseData.LiveDataProvider>
    </AssetHealthData.LiveDataProvider>
  );
};

export function AssetLiveDataRefreshButton() {
  return <AssetBaseData.LiveDataRefresh />;
}

export function __resetForJest() {
  __resetBaseData();
  __resetStaleData();
  __resetHealthData();
}
