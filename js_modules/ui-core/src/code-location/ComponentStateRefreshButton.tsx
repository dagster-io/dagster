import {Button, Icon, Spinner, showToast} from '@dagster-io/ui-components';
import {useCallback, useEffect, useRef, useState} from 'react';

import {useApolloClient, useMutation} from '../apollo-client';
import {CODE_LOCATION_COMPONENTS_QUERY} from './CodeLocationComponentsQuery';
import {LATEST_DEFS_STATE_INFO_QUERY} from './LatestDefsStateInfoQuery';
import {REFRESH_COMPONENT_STATE_MUTATION} from './RefreshComponentStateMutation';
import {
  LatestDefsStateInfoQuery,
  LatestDefsStateInfoQueryVariables,
} from './types/LatestDefsStateInfoQuery.types';
import {
  RefreshComponentStateMutation,
  RefreshComponentStateMutationVariables,
} from './types/RefreshComponentStateMutation.types';

interface Props {
  locationName: string;
  defsStateKey: string;
  // Version visible to the user when they clicked refresh. Polling watches for
  // ``defsStateInfo.version`` to change from this value; ``null`` means no
  // state has been written yet for the key, in which case any non-null version
  // counts as the bump.
  previousVersion: string | null;
}

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 5 * 60 * 1000;

/**
 * Refresh-state action for a single state-backed component. Caller should only
 * render this for ``VERSIONED_STATE_STORAGE`` components — refresh isn't
 * meaningful for local-filesystem or legacy-code-server state.
 *
 * The server mutation waits a bounded window for the agent. Fast successes
 * and fast failures return synchronously and are handled inline. If the wait
 * elapses first, the server returns ``Accepted`` and we poll
 * ``latestDefsStateInfo`` until the version on this key bumps from
 * ``previousVersion`` (or a frontend-side ceiling fires).
 */
export const ComponentStateRefreshButton = ({
  locationName,
  defsStateKey,
  previousVersion,
}: Props) => {
  const client = useApolloClient();
  const [isPolling, setIsPolling] = useState(false);
  const cancelledRef = useRef(false);

  const [refresh, {loading: mutating}] = useMutation<
    RefreshComponentStateMutation,
    RefreshComponentStateMutationVariables
  >(REFRESH_COMPONENT_STATE_MUTATION, {
    refetchQueries: [{query: CODE_LOCATION_COMPONENTS_QUERY, variables: {locationName}}],
    awaitRefetchQueries: true,
  });

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
    };
  }, []);

  const pollUntilVersionChanges = useCallback(async () => {
    setIsPolling(true);
    const startedAt = Date.now();
    try {
      while (!cancelledRef.current) {
        if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
          showToast({
            intent: 'warning',
            message:
              "Refresh didn't complete within 5 minutes. Check the agent or code server logs.",
          });
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
        if (cancelledRef.current) {
          return;
        }
        const {data} = await client.query<
          LatestDefsStateInfoQuery,
          LatestDefsStateInfoQueryVariables
        >({
          query: LATEST_DEFS_STATE_INFO_QUERY,
          fetchPolicy: 'network-only',
        });
        const entry = data.latestDefsStateInfo?.keyStateInfo?.find((e) => e?.name === defsStateKey);
        const newVersion = entry?.info?.version ?? null;
        if (newVersion && newVersion !== previousVersion) {
          showToast({intent: 'success', message: 'Refreshed component state.'});
          // Pull fresh row data so the version column updates in place. The
          // backend overlays storage on top of the cached snapshot, so this
          // reflects the new version without a code-location reload.
          await client.refetchQueries({
            include: [CODE_LOCATION_COMPONENTS_QUERY],
          });
          return;
        }
      }
    } finally {
      setIsPolling(false);
    }
  }, [client, defsStateKey, previousVersion]);

  const handleRefresh = useCallback(async () => {
    try {
      const result = await refresh({variables: {locationName, defsStateKey}});
      const payload = result.data?.refreshComponentState;
      switch (payload?.__typename) {
        case 'RefreshComponentStateSuccess':
          showToast({intent: 'success', message: 'Refreshed component state.'});
          break;
        case 'RefreshComponentStateAccepted':
          await pollUntilVersionChanges();
          break;
        case 'RefreshComponentStateError':
        case 'UnauthorizedError':
        case 'PythonError':
          showToast({intent: 'danger', message: payload.message});
          break;
      }
    } catch (e) {
      showToast({
        intent: 'danger',
        message: e instanceof Error ? e.message : 'Failed to refresh state.',
      });
    }
  }, [defsStateKey, locationName, pollUntilVersionChanges, refresh]);

  const loading = mutating || isPolling;
  const label = isPolling ? 'Still refreshing…' : mutating ? 'Refreshing…' : 'Refresh';
  return (
    <Button
      icon={loading ? <Spinner purpose="body-text" /> : <Icon name="refresh" />}
      disabled={loading}
      onClick={handleRefresh}
    >
      {label}
    </Button>
  );
};
