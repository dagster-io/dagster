import {NetworkStatus, ObservableQuery, QueryResult} from '@apollo/client';
import {RefreshableCountdown, useCountdown} from '@dagster-io/ui-components';
import {useCallback, useEffect, useMemo, useRef, useState} from 'react';

import {useDocumentVisibility} from '../hooks/useDocumentVisibility';
import {isSearchVisible, useSearchVisibility} from '../search/useSearchVisibility';

export const FIFTEEN_SECONDS = 15 * 1000;
export const ONE_MONTH = 30 * 24 * 60 * 60 * 1000;

export interface QueryRefreshState {
  nextFireMs: number | null | undefined;
  nextFireDelay: number; // seconds
  networkStatus: NetworkStatus;
  refetch: ObservableQuery['refetch'];
}

export interface RefreshState<T = void> {
  nextFireMs: number | null | undefined;
  nextFireDelay: number; // seconds
  refetch: () => Promise<T>;
  loading: boolean;
}

/**
 * The default pollInterval feature of Apollo's useQuery is fine, but we want to add two features:
 *
 * - If you switch tabs in Chrome and the document is no longer visible, don't refresh anything.
 *   Just refresh immediately when you click back to the tab.
 * - If a request takes more than 1/4 of the requested poll interval (eg: an every-20s query takes 5s),
 *   poll more slowly.
 *
 * You can choose to use this hook alone (no UI) or pass the returned refreshState object to
 * <QueryRefreshCountdown /> to display the refresh status.
 *
 * Important: Required useQuery Options:
 *
 * - When using this hook, pass useQuery the `notifyOnNetworkStatusChange: true` option.
 *   This allows the hook to observe how long the request spends in-flight. This option
 *   is NOT necessary if you pass cache-and-network, but IS necessary if you use network-only
 *   or the default cache-first fetchPolicy.
 *
 */
export function useQueryRefreshAtInterval(
  queryResult: Pick<QueryResult<any, any>, 'refetch' | 'loading' | 'networkStatus'>,
  intervalMs: number,
  enabled = true,
) {
  // Sanity check - don't use this hook alongside a useQuery pollInterval
  if (queryResult.networkStatus === NetworkStatus.poll) {
    throw new Error(
      'useQueryRefreshAtInterval is meant to replace useQuery<>({pollInterval}). Remove the pollInterval!',
    );
  }

  const {nextFireMs, nextFireDelay, refetch} = useRefreshAtInterval({
    refresh: useCallback(async () => {
      return await queryResult?.refetch();
    }, [queryResult]),
    intervalMs,
    enabled,
  });

  // Memoize the returned object so components passed the entire QueryRefreshState
  // can be memoized / pure components.
  return useMemo<QueryRefreshState>(
    () => ({
      nextFireMs,
      nextFireDelay,
      networkStatus: queryResult.networkStatus,
      refetch,
    }),
    [nextFireMs, nextFireDelay, queryResult.networkStatus, refetch],
  );
}

export function useRefreshAtInterval<T = void>({
  refresh,
  intervalMs,
  enabled = true,
  leading,
}: {
  refresh: () => Promise<T>;
  intervalMs: number;
  enabled?: boolean;
  leading?: boolean;
}) {
  const timer = useRef<number>();
  const loadingStartMs = useRef<number>();
  const [nextFireMs, setNextFireMs] = useState<number | null>();

  // If the page is in the background when our refresh timer fires, we set
  // documentVisiblityDidInterrupt = true. When the document becomes visible again,
  // this effect triggers an immediate out-of-interval refresh.
  const documentVisiblityDidInterrupt = useRef(false);
  const documentVisible = useDocumentVisibility();

  const searchVisibilityDidInterrupt = useRef(false);
  const searchVisible = useSearchVisibility();

  const didMakeLeadingQuery = useRef(false);

  const [loading, setLoading] = useState(false);

  const refreshFn = useCallback(async () => {
    setLoading(true);
    const result = await refresh();
    setLoading(false);
    return result;
  }, [refresh]);

  useEffect(() => {
    // Whenever the refresh function changes we need to refire the leading query
    if (leading) {
      didMakeLeadingQuery.current = false;
    }
  }, [leading, refreshFn]);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    if (
      documentVisible &&
      !searchVisible &&
      (searchVisibilityDidInterrupt.current ||
        documentVisiblityDidInterrupt.current ||
        (leading && !didMakeLeadingQuery.current))
    ) {
      refreshFn();
      documentVisiblityDidInterrupt.current = false;
      searchVisibilityDidInterrupt.current = false;
      didMakeLeadingQuery.current = true;
    }
  }, [documentVisible, enabled, searchVisible, refreshFn, leading]);

  useEffect(() => {
    clearTimeout(timer.current);
    if (!enabled) {
      return;
    }

    // If the query has just transitioned to a `loading` state, capture the current
    // time so we can compute the elapsed time when the query completes, and exit.
    if (loading) {
      loadingStartMs.current = loadingStartMs.current || Date.now();
      return;
    }

    // If the query is no longer `loading`, determine elapsed time and decide
    // when to refresh. If the query took > 1/4 the desired interval, delay
    // the next tick to give the server some slack.
    const queryDurationMs = loadingStartMs.current ? Date.now() - loadingStartMs.current : 0;
    const adjustedIntervalMs = Math.max(intervalMs, queryDurationMs * 4);

    // To test that the UI reflects the next fire date correctly, try this:
    // const adjustedIntervalMs = Math.max(3, Math.random() * 30) * 1000;

    setNextFireMs(Date.now() + adjustedIntervalMs);
    loadingStartMs.current = undefined;

    // Schedule the next refretch
    timer.current = window.setTimeout(() => {
      if (document.visibilityState === 'hidden') {
        // If the document is no longer visible, mark that we have skipped an update rather
        // then updating in the background. We'll refresh when we return to the foreground.
        documentVisiblityDidInterrupt.current = true;
        return;
      }
      if (isSearchVisible()) {
        searchVisibilityDidInterrupt.current = true;
        return;
      }
      refreshFn();
    }, adjustedIntervalMs);

    return () => {
      clearTimeout(timer.current);
    };
  }, [loading, intervalMs, enabled, refreshFn]);

  // Expose the next fire time both as a unix timstamp and as a "seconds" interval
  // so the <QueryRefreshCountdown> can display the number easily.
  const nextFireDelay = useMemo(() => (nextFireMs ? nextFireMs - Date.now() : -1), [nextFireMs]);

  // Memoize the returned object so components passed the entire QueryRefreshState
  // can be memoized / pure components.
  return useMemo<RefreshState<T>>(
    () => ({
      loading,
      nextFireMs,
      nextFireDelay,
      refetch: refreshFn,
    }),
    [loading, nextFireMs, nextFireDelay, refreshFn],
  );
}

/**
 * This hook allows you to hook a single QueryRefreshCountdown component to more than
 * one useQueryRefreshAtInterval. The QueryRefreshCountdown will reflect the countdown
 * state of the FIRST query, but clicking the refresh button will trigger them all.
 *
 * Note: If you use this hook, you should pass the same interval to each
 * useQueryRefreshAtInterval.
 */
export function useMergedRefresh(
  ...args: [QueryRefreshState, ...QueryRefreshState[]]
): QueryRefreshState {
  return useMemo(() => {
    const refetch: ObservableQuery['refetch'] = async () => {
      const [ar] = await Promise.all(args.map((s) => s?.refetch()));
      return ar!;
    };
    return {
      nextFireMs: args[0].nextFireMs,
      nextFireDelay: args[0].nextFireDelay,
      networkStatus: args[0].networkStatus,
      refetch,
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, args);
}

export const QueryRefreshCountdown = ({
  refreshState,
  dataDescription,
}: {
  refreshState: QueryRefreshState | RefreshState;
  dataDescription?: string;
}) => {
  const status = (
    'networkStatus' in refreshState
      ? refreshState.networkStatus === NetworkStatus.ready
      : !refreshState.loading
  )
    ? 'counting'
    : 'idle';
  const timeRemaining = useCountdown({duration: refreshState.nextFireDelay, status});

  return (
    <RefreshableCountdown
      refreshing={status === 'idle' || timeRemaining === 0}
      seconds={Math.floor(timeRemaining / 1000)}
      onRefresh={() => refreshState.refetch()}
      dataDescription={dataDescription}
    />
  );
};
