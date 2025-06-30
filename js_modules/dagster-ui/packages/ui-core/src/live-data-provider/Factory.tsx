import React from 'react';

import {
  LiveDataProvider,
  LiveDataRefresh,
  useLiveData,
  useLiveDataSingle,
} from './LiveDataProvider';
import {LiveDataThreadID} from './LiveDataThread';
import {LiveDataThreadManager} from './LiveDataThreadManager';

export function liveDataFactory<T, R>(
  useHooks: () => R,
  queryKeys: (keys: string[], result: R) => Promise<Record<string, T>>,
  batchSize?: number,
  parallelFetches?: number,
) {
  const resultsFromUseHook: {current: R | undefined} = {current: undefined};
  const manager = new LiveDataThreadManager(
    (keys: string[]) => {
      if (!resultsFromUseHook.current) {
        throw new Error(
          'Expected LiveDataProvider to have been in the DOM by the time queryKeys is called',
        );
      }
      return queryKeys(keys, resultsFromUseHook.current);
    },
    batchSize,
    parallelFetches,
  );

  const LiveDataRefreshContext = React.createContext<{
    isGloballyRefreshing: boolean;
    oldestDataTimestamp: number;
    refresh: () => void;
  }>({
    isGloballyRefreshing: false,
    oldestDataTimestamp: Infinity,
    refresh: () => {},
  });

  return {
    LiveDataProvider: ({children}: {children: React.ReactNode}) => {
      resultsFromUseHook.current = useHooks();
      return (
        <LiveDataProvider manager={manager} LiveDataRefreshContext={LiveDataRefreshContext}>
          {children}
        </LiveDataProvider>
      );
    },
    useLiveData: (keys: string[], thread: LiveDataThreadID = 'default', skip?: boolean) => {
      return useLiveData<T>(keys, manager, thread, skip);
    },
    useLiveDataSingle: (key: string, thread: LiveDataThreadID = 'default', skip?: boolean) => {
      return useLiveDataSingle<T>(key, manager, thread, skip);
    },
    manager,
    LiveDataRefresh: () => <LiveDataRefresh LiveDataRefreshContext={LiveDataRefreshContext} />,
  };
}
