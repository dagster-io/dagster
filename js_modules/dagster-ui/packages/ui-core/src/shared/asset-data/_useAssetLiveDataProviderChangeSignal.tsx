import uniq from 'lodash/uniq';
import React, {useReducer, useRef} from 'react';

import {AssetAutomationData} from '../../asset-data/AssetAutomationDataProvider';
import {AssetBaseData} from '../../asset-data/AssetBaseDataProvider';
import {AssetHealthData} from '../../asset-data/AssetHealthDataProvider';
import {AssetStaleStatusData} from '../../asset-data/AssetStaleStatusDataProvider';
import {observeAssetEventsInRuns} from '../../asset-graph/AssetRunLogObserver';
import {tokenForAssetKey} from '../../asset-graph/Utils';
import {useThrottledEffect} from '../../hooks/useThrottledEffect';
import {SUBSCRIPTION_MAX_POLL_RATE} from '../../live-data-provider/util';
import {useDidLaunchEvent} from '../../runs/RunUtils';

export const useAssetLiveDataProviderChangeSignal = () => {
  useDidLaunchEvent(() => {
    AssetStaleStatusData.manager.invalidateCache();
    AssetBaseData.manager.invalidateCache();
    AssetHealthData.manager.invalidateCache();
    AssetAutomationData.manager.invalidateCache();
  }, SUBSCRIPTION_MAX_POLL_RATE);

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

  useThrottledEffect(
    () => {
      const assetKeyTokensArray = [
        ...staleKeysObserved.current.flatMap((keySet) => Array.from(keySet)),
        ...baseKeysObserved.current.flatMap((keySet) => Array.from(keySet)),
        ...healthKeysObserved.current.flatMap((keySet) => Array.from(keySet)),
      ];
      const assetKeyTokens = new Set(assetKeyTokensArray);
      const dataForObservedKeys = assetKeyTokensArray
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
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
          AssetAutomationData.manager.invalidateCache();
        }
      });
      return unobserve;
    },
    [keysChanged],
    2000,
  );
};
