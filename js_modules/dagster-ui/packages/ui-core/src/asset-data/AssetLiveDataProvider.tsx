import React, {useCallback, useMemo} from 'react';
import {useAssetLiveDataProviderChangeSignal} from 'shared/asset-data/_useAssetLiveDataProviderChangeSignal.oss';

import {
  AssetAutomationData,
  __resetForJest as __resetAutomationData,
} from './AssetAutomationDataProvider';
import {AssetBaseData, __resetForJest as __resetBaseData} from './AssetBaseDataProvider';
import {AssetHealthData, __resetForJest as __resetHealthData} from './AssetHealthDataProvider';
import {
  AssetStaleStatusData,
  __resetForJest as __resetStaleData,
} from './AssetStaleStatusDataProvider';
import {LiveDataForNodeWithStaleData, tokenForAssetKey} from '../asset-graph/Utils';
import {SelectionHealthDataProvider} from '../assets/catalog/useSelectionHealthData';
import {AssetKeyInput} from '../graphql/types';
import {LiveDataPollRateContext} from '../live-data-provider/LiveDataProvider';
import {LiveDataThreadID} from '../live-data-provider/LiveDataThread';

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
  const pollRate = React.useContext(LiveDataPollRateContext);

  React.useEffect(() => {
    AssetStaleStatusData.manager.setPollRate(pollRate);
    AssetBaseData.manager.setPollRate(pollRate);
    AssetHealthData.manager.setPollRate(pollRate);
    AssetAutomationData.manager.setPollRate(pollRate);
  }, [pollRate]);

  useAssetLiveDataProviderChangeSignal();

  return (
    <AssetAutomationData.LiveDataProvider>
      <AssetHealthData.LiveDataProvider>
        <AssetBaseData.LiveDataProvider>
          <AssetStaleStatusData.LiveDataProvider>
            <SelectionHealthDataProvider>{children}</SelectionHealthDataProvider>
          </AssetStaleStatusData.LiveDataProvider>
        </AssetBaseData.LiveDataProvider>
      </AssetHealthData.LiveDataProvider>
    </AssetAutomationData.LiveDataProvider>
  );
};

export function AssetLiveDataRefreshButton() {
  return <AssetBaseData.LiveDataRefresh />;
}

export function __resetForJest() {
  __resetBaseData();
  __resetStaleData();
  __resetHealthData();
  __resetAutomationData();
}
