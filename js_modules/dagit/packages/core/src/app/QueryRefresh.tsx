import {NetworkStatus, ObservableQuery, QueryResult} from '@apollo/client';
import {useCountdown, RefreshableCountdown} from '@dagster-io/ui';
import * as React from 'react';

import {useDocumentVisibility} from '../hooks/useDocumentVisibility';

export const FIFTEEN_SECONDS = 15 * 1000;

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
 */
export function useQueryRefreshAtInterval(queryResult: QueryResult<any, any>, intervalMs: number) {
  const timer = React.useRef<number>();
  const loadingStartMs = React.useRef<number>();
  const [nextFireMs, setNextFireMs] = React.useState<number | null>();

  const queryResultRef = React.useRef(queryResult);
  queryResultRef.current = queryResult;

  if (queryResult.networkStatus === NetworkStatus.poll) {
    throw new Error(
      'useQueryRefreshAtInterval is meant to replace useQuery({pollInterval}). Remove the pollInterval!',
    );
  }

  const documentVisible = useDocumentVisibility();
  const documentVisiblityDidInterrupt = React.useRef(false);

  React.useEffect(() => {
    if (documentVisible && documentVisiblityDidInterrupt.current) {
      queryResultRef.current?.refetch();
      documentVisiblityDidInterrupt.current = false;
    }
  }, [documentVisible]);

  React.useEffect(() => {
    clearTimeout(timer.current);

    if (queryResult.loading) {
      loadingStartMs.current = loadingStartMs.current || Date.now();
      return;
    }

    const queryDurationMs = loadingStartMs.current ? Date.now() - loadingStartMs.current : 0;
    const adjustedIntervalMs = Math.max(intervalMs, queryDurationMs * 3);

    // To test that the UI reflects the next fire date correctly, try this:
    // const adjustedIntervalMs = Math.max(3, Math.random() * 30) * 1000;

    setNextFireMs(Date.now() + adjustedIntervalMs);
    loadingStartMs.current = undefined;

    timer.current = window.setTimeout(() => {
      if (document.hidden) {
        documentVisiblityDidInterrupt.current = true;
        return;
      }
      queryResultRef.current?.refetch();
    }, adjustedIntervalMs);

    return () => {
      clearTimeout(timer.current);
    };
  }, [queryResult.loading, intervalMs]);

  const nextFireDelay = React.useMemo(() => (nextFireMs ? nextFireMs - Date.now() : -1), [
    nextFireMs,
  ]);

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

export const QueryRefreshCountdown = ({refreshState}: {refreshState: QueryRefreshState}) => {
  const status = refreshState.networkStatus === NetworkStatus.ready ? 'counting' : 'idle';
  const timeRemaining = useCountdown({duration: refreshState.nextFireDelay, status});

  return (
    <RefreshableCountdown
      refreshing={status === 'idle' || timeRemaining === 0}
      seconds={Math.floor(timeRemaining / 1000)}
      onRefresh={() => refreshState.refetch()}
    />
  );
};
