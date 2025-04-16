import React, {useMemo} from 'react';

import {LiveDataRefreshButton} from './LiveDataRefreshButton';
import {LiveDataThreadID} from './LiveDataThread';
import {LiveDataThreadManager} from './LiveDataThreadManager';
import {useDocumentVisibility} from '../hooks/useDocumentVisibility';

export const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;

export const LiveDataPollRateContext = React.createContext<number>(SUBSCRIPTION_IDLE_POLL_RATE);

export function useLiveDataSingle<T>(
  key: string,
  manager: LiveDataThreadManager<T>,
  thread: LiveDataThreadID = 'default',
) {
  const {liveDataByNode, refresh, refreshing} = useLiveData(
    React.useMemo(() => [key], [key]),
    manager,
    thread,
  );
  return {
    liveData: liveDataByNode[key],
    refresh,
    refreshing,
  };
}

const emptyObject = {};

export function useLiveData<T>(
  keys: string[],
  manager: LiveDataThreadManager<T>,
  thread: LiveDataThreadID = 'default',
  batchUpdatesInterval: number = 1000,
) {
  const [data, setData] = React.useState<Record<string, T>>({});

  const [isRefreshing, setIsRefreshing] = React.useState(false);

  React.useLayoutEffect(() => {
    let timeout: ReturnType<typeof setTimeout> | null = null;
    let didUpdateOnce = false;
    let didScheduleUpdateOnce = false;
    let updates: {stringKey: string; data: T | undefined}[] = [];
    const id = Math.random();
    console.log('resetting data');;
    // reset data to empty object
    setData(emptyObject);

    function processUpdates() {
      if (!updates.length) {
        return;
      }
      setData((current) => {
        const copy = {...current};
        updates.forEach(({stringKey, data}) => {
          if (data) {
            copy[stringKey] = data;
          } else {
            delete copy[stringKey];
          }
        });
        updates = [];
        return copy;
      });
    }

    const setDataSingle = (stringKey: string, messageId: number, data?: T | undefined) => {
      if (messageId !== id) {
        // We do a lot of scheduling of updates downstream which means this could be called with an older id.
        // corresponding to a different set of keys. In this case, we just skip the update.
        return;
      }
      /**
       * Throttle updates to avoid triggering too many GCs and too many updates when fetching 1,000 assets,
       */
      updates.push({stringKey, data});
      if (!didUpdateOnce) {
        if (!didScheduleUpdateOnce) {
          didScheduleUpdateOnce = true;
          requestAnimationFrame(() => {
            processUpdates();
            didUpdateOnce = true;
          });
        }
      } else if (!timeout) {
        timeout = setTimeout(() => {
          processUpdates();
          timeout = null;
        }, batchUpdatesInterval);
      }
    };
    const unsubscribeCallbacks = keys.map((key) =>
      manager.subscribe(key, (stringKey, data) => setDataSingle(stringKey, id, data), thread),
    );
    return () => {
      unsubscribeCallbacks.forEach((cb) => {
        cb();
      });
    };
  }, [keys, batchUpdatesInterval, manager, thread]);

  return {
    liveDataByNode: data,

    refresh: React.useCallback(() => {
      manager.invalidateCache(keys);
      setIsRefreshing(true);
    }, [keys, manager]),

    refreshing: React.useMemo(() => {
      if (isRefreshing && !manager.areKeysRefreshing(keys)) {
        setTimeout(() => {
          setIsRefreshing(false);
        });
        return false;
      }
      return true;
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [keys, data, isRefreshing]),
  };
}

const LiveDataProviderTyped = <T,>({
  children,
  LiveDataRefreshContext,
  manager,
}: {
  children: React.ReactNode;
  LiveDataRefreshContext: React.Context<{
    isGloballyRefreshing: boolean;
    oldestDataTimestamp: number;
    refresh: () => void;
  }>;
  manager: LiveDataThreadManager<T>;
}) => {
  const [isGloballyRefreshing, setIsGloballyRefreshing] = React.useState(false);
  const [oldestDataTimestamp, setOldestDataTimestamp] = React.useState(0);

  const onUpdatingOrUpdated = React.useCallback(() => {
    const {isRefreshing, oldestDataTimestamp} = manager.getOldestDataTimestamp();
    setIsGloballyRefreshing(isRefreshing);
    setOldestDataTimestamp(oldestDataTimestamp);
  }, [manager]);

  React.useEffect(() => {
    manager.setOnUpdatingOrUpdated(onUpdatingOrUpdated);
  }, [manager, onUpdatingOrUpdated]);

  const isDocumentVisible = useDocumentVisibility();
  React.useEffect(() => {
    manager.onDocumentVisiblityChange(isDocumentVisible);
  }, [manager, isDocumentVisible]);

  return (
    <LiveDataRefreshContext.Provider
      value={useMemo(
        () => ({
          isGloballyRefreshing,
          oldestDataTimestamp,
          refresh: () => {
            manager.invalidateCache();
          },
        }),
        [isGloballyRefreshing, oldestDataTimestamp, manager],
      )}
    >
      {children}
    </LiveDataRefreshContext.Provider>
  );
};

export const LiveDataProvider = React.memo(LiveDataProviderTyped) as typeof LiveDataProviderTyped;

export function LiveDataRefresh({
  LiveDataRefreshContext,
}: {
  LiveDataRefreshContext: React.Context<{
    isGloballyRefreshing: boolean;
    oldestDataTimestamp: number;
    refresh: () => void;
  }>;
}) {
  const {isGloballyRefreshing, oldestDataTimestamp, refresh} =
    React.useContext(LiveDataRefreshContext);
  return (
    <LiveDataRefreshButton
      isRefreshing={isGloballyRefreshing}
      oldestDataTimestamp={oldestDataTimestamp}
      onRefresh={refresh}
    />
  );
}
