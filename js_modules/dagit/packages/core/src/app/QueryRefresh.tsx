import {NetworkStatus, ObservableQuery, QueryResult} from '@apollo/client';
import {useCountdown, RefreshableCountdown} from '@dagster-io/ui';
import * as React from 'react';

import {useDocumentVisibility} from '../hooks/useDocumentVisibility';

export const FIFTEEN_SECONDS = 15 * 1000;
export const ONE_MONTH = 30 * 24 * 60 * 60 * 1000;

export interface QueryRefreshState {
  nextFireMs: number | null | undefined;
  nextFireDelay: number; // seconds
  networkStatus: NetworkStatus;
  refetch: ObservableQuery['refetch'];
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
export function useQueryRefreshAtInterval(queryResult: QueryResult<any, any>, intervalMs: number) {
  const timer = React.useRef<number>();
  const loadingStartMs = React.useRef<number>();
  const [nextFireMs, setNextFireMs] = React.useState<number | null>();

  const queryResultRef = React.useRef(queryResult);
  queryResultRef.current = queryResult;

  // Sanity check - don't use this hook alongside a useQuery pollInterval
  if (queryResult.networkStatus === NetworkStatus.poll) {
    throw new Error(
      'useQueryRefreshAtInterval is meant to replace useQuery({pollInterval}). Remove the pollInterval!',
    );
  }

  // If the page is in the background when our refresh timer fires, we set
  // documentVisiblityDidInterrupt = true. When the document becomes visible again,
  // this effect triggers an immediate out-of-interval refresh.
  const documentVisiblityDidInterrupt = React.useRef(false);
  const documentVisible = useDocumentVisibility();

  React.useEffect(() => {
    if (documentVisible && documentVisiblityDidInterrupt.current) {
      queryResultRef.current?.refetch();
      documentVisiblityDidInterrupt.current = false;
    }
  }, [documentVisible]);

  React.useEffect(() => {
    clearTimeout(timer.current);

    // If the query has just transitioned to a `loading` state, capture the current
    // time so we can compute the elapsed time when the query completes, and exit.
    if (queryResult.loading) {
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
      queryResultRef.current?.refetch();
    }, adjustedIntervalMs);

    return () => {
      clearTimeout(timer.current);
    };
  }, [queryResult.loading, intervalMs]);

  // Expose the next fire time both as a unix timstamp and as a "seconds" interval
  // so the <QueryRefreshCountdown> can display the number easily.
  const nextFireDelay = React.useMemo(() => (nextFireMs ? nextFireMs - Date.now() : -1), [
    nextFireMs,
  ]);

  // Memoize the returned object so components passed the entire QueryRefreshState
  // can be memoized / pure components.
  return React.useMemo<QueryRefreshState>(
    () => ({
      nextFireMs,
      nextFireDelay,
      networkStatus: queryResult.networkStatus,
      refetch: queryResult.refetch,
    }),
    [nextFireMs, nextFireDelay, queryResult.networkStatus, queryResult.refetch],
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
  return React.useMemo(() => {
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
  refreshState: QueryRefreshState;
  dataDescription?: string;
}) => {
  const status = refreshState.networkStatus === NetworkStatus.ready ? 'counting' : 'idle';
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
