import min from 'lodash/min';
import uniq from 'lodash/uniq';
import uniqBy from 'lodash/uniqBy';
import React, {useCallback, useEffect, useMemo, useState} from 'react';

import {clipEventsToSharedMinimumTime} from './clipEventsToSharedMinimumTime';
import {AssetKey, AssetViewParams} from './types';
import {
  AssetEventsQuery,
  AssetEventsQueryVariables,
  AssetMaterializationFragment,
  AssetObservationFragment,
} from './types/useRecentAssetEvents.types';
import {ASSET_EVENTS_QUERY} from './useRecentAssetEvents';
import {useApolloClient} from '../apollo-client';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';

/** Note: This hook paginates through an asset's events, optionally beginning at ?asOf=.
 * This could re-use useCursorPaginatedQuery in the future if we made the API use a `cursor`
 * var instead of `before` but we also want this hook to refresh the results when new events
 * arrive without discarding your pagination state.
 *
 * This hook exposes both a `fetchMore` and a `fetchLatest`, and we take advantage of the
 * fact that the events are a write-only log - we can safely re-fetch the latest events
 * and as long as we de-dupe we're ok!
 *
 * This hook expects that `useGroupedEvents` will do the sorting downstream.
 */
export function usePaginatedAssetEvents(
  assetKey: AssetKey | undefined,
  params: Pick<AssetViewParams, 'asOf'>,
) {
  const initialAsOf = params.asOf ? `${Number(params.asOf) + 1}` : undefined;

  const [observations, setObservations] = React.useState<AssetObservationFragment[]>([]);
  const [materializations, setMaterializations] = React.useState<AssetMaterializationFragment[]>(
    [],
  );

  const client = useApolloClient();
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setObservations([]);
    setMaterializations([]);
  }, [assetKey]);

  const fetch = useCallback(
    async (before = initialAsOf) => {
      if (!assetKey) {
        return;
      }
      setLoading(true);
      const {data} = await client.query<AssetEventsQuery, AssetEventsQueryVariables>({
        query: ASSET_EVENTS_QUERY,
        variables: {
          assetKey: {path: assetKey.path},
          limit: 100,
          before,
        },
      });
      setLoading(false);

      const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;

      const {materializations, observations} = clipEventsToSharedMinimumTime(
        asset?.assetMaterializations || [],
        asset?.assetObservations || [],
        100,
      );

      setLoaded(true);
      setMaterializations((loaded) =>
        uniqBy([...loaded, ...materializations], (e) => `${e.runId}${e.timestamp}`),
      );
      setObservations((loaded) =>
        uniqBy([...loaded, ...observations], (e) => `${e.runId}${e.timestamp}`),
      );
    },
    [assetKey, client, initialAsOf],
  );

  useBlockTraceUntilTrue('AssetEventsQuery', loaded);

  return useMemo(() => {
    const all = [...materializations, ...observations];

    // Note: If we "discover" more partition keys of a non-SDA as more events are loaded, we want
    // those to be appended to the end so things don't jump around, so there is no sort() here.
    const loadedPartitionKeys = uniq(all.map((p) => p.partition!).filter(Boolean)).reverse();

    return {
      loading,
      materializations,
      observations,
      loadedPartitionKeys,
      fetchLatest: fetch,
      fetchMore: () => fetch(`${min(all.map((e) => Number(e.timestamp)))}`),
    };
  }, [materializations, observations, loading, fetch]);
}
