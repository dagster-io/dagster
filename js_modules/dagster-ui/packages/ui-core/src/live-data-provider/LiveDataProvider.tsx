import React, {useLayoutEffect, useMemo} from 'react';

import {LiveDataRefreshButton} from './LiveDataRefreshButton';
import {LiveDataThreadID} from './LiveDataThread';
import {LiveDataThreadManager} from './LiveDataThreadManager';
import {useDocumentVisibility} from '../hooks/useDocumentVisibility';
import {useStableReferenceByHash} from '../hooks/useStableReferenceByHash';

export const SUBSCRIPTION_IDLE_POLL_RATE = 30 * 1000;

export const LiveDataPollRateContext = React.createContext<number>(SUBSCRIPTION_IDLE_POLL_RATE);

export function useLiveDataSingle<T>(
  key: string,
  manager: LiveDataThreadManager<T>,
  thread: LiveDataThreadID = 'default',
  skip?: boolean,
) {
  const {liveDataByNode, refresh, refreshing} = useLiveData(
    React.useMemo(() => [key], [key]),
    manager,
    thread,
    skip,
  );
  return {
    liveData: liveDataByNode[key],
    refresh,
    refreshing,
  };
}

const emptyObject = {};
let uuid = 0;

export function useLiveData<T>(
  _keys: string[],
  manager: LiveDataThreadManager<T>,
  thread: LiveDataThreadID = 'default',
  skip?: boolean,
  batchUpdatesInterval: number = 1000,
) {
  const [data, setData] = React.useState<Record<string, T>>(emptyObject);

  const [isRefreshing, setIsRefreshing] = React.useState(false);

  // Hash the keys and use that as a dependency to avoid unsubscribing/re-subscribing to the same keys in case the reference changes but the keys are the same
  const keys = useStableReferenceByHash(_keys);

  const initialSkipRef = React.useRef(skip);
  const uuidRef = React.useRef(0);

  const updateManager = useMemo(() => {
    let timeout: ReturnType<typeof setTimeout> | null = null;
    let didUpdateOnce = false;
    let didScheduleUpdateOnce = false;
    let updates: {stringKey: string; data: T | undefined}[] = [];

    let shouldSkip = initialSkipRef.current;

    function processUpdates() {
      if (!updates.length || shouldSkip) {
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

    const queueUpdate = (stringKey: string, messageId: number, data?: T | undefined) => {
      if (messageId !== uuidRef.current) {
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

    return {
      queueUpdate,
      processUpdates,
      setSkip: (skip: boolean) => {
        shouldSkip = skip;
      },
    };
  }, [batchUpdatesInterval]);

  useLayoutEffect(() => {
    updateManager.setSkip(skip ?? false);
  }, [skip, updateManager]);

  React.useLayoutEffect(() => {
    const id = uuid++;
    uuidRef.current = id;
    // reset data to empty object
    setData(emptyObject);

    const unsubscribeCallbacks = keys.map((key) =>
      manager.subscribe(
        key,
        (stringKey, data) => updateManager.queueUpdate(stringKey, id, data),
        thread,
      ),
    );

    updateManager.processUpdates();
    return () => {
      unsubscribeCallbacks.forEach((cb) => {
        cb();
      });
    };
  }, [keys, manager, thread, updateManager]);

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
