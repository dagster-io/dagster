import min from 'lodash/min';
import uniq from 'lodash/uniq';
import uniqBy from 'lodash/uniqBy';
import React, {useCallback, useEffect, useMemo, useState} from 'react';

import {clipEventsToSharedMinimumTime} from './clipEventsToSharedMinimumTime';
import {AssetKey, AssetViewParams} from './types';
import {
  AssetEventsQuery,
  AssetEventsQueryVariables,
  AssetObservationFragment,
} from './types/useRecentAssetEvents.types';
import {ASSET_EVENTS_QUERY, AssetMaterializationFragment} from './useRecentAssetEvents';
import {useApolloClient} from '../apollo-client';
import {MaterializationHistoryEventTypeSelector} from '../graphql/types';
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
  params: Pick<AssetViewParams, 'asOf'> & {
    before?: number;
    after?: number;
    partitions?: string[];
    status?: MaterializationHistoryEventTypeSelector;
  },
) {
  const initialAsOf = params.asOf ? `${Number(params.asOf) + 1}` : undefined;
  const afterParam = params.after ? `${params.after + 1}` : undefined;
  const beforeParam = params.before ? `${params.before - 1}` : undefined;

  const [observations, setObservations] = React.useState<AssetObservationFragment[]>([]);
  const [materializations, setMaterializations] = React.useState<AssetMaterializationFragment[]>(
    [],
  );

  const client = useApolloClient();
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [cursor, setCursor] = useState<string | undefined>(undefined);

  useEffect(() => {
    setObservations([]);
    setMaterializations([]);
    setCursor(undefined);
  }, [assetKey, params.before, params.after, params.partitions, params.status]);

  const fetch = useCallback(
    async (before = initialAsOf ?? beforeParam, cursor: string | undefined = undefined) => {
      if (!assetKey) {
        return;
      }
      setLoading(true);
      const {data} = await client.query<AssetEventsQuery, AssetEventsQueryVariables>({
        query: ASSET_EVENTS_QUERY,
        variables: {
          assetKey: {path: assetKey.path},
          limit: 100,
          cursor,
          before,
          after: afterParam,
          partitions: params.partitions,
          eventTypeSelector: params.status ?? MaterializationHistoryEventTypeSelector.ALL,
        },
      });
      setLoading(false);

      const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;

      const {materializations, observations} = clipEventsToSharedMinimumTime(
        asset?.assetMaterializationHistory?.results || [],
        asset?.assetObservations.results || [],
        100,
      );

      setLoaded(true);
      setMaterializations((loaded) =>
        uniqBy([...loaded, ...materializations], (e) => `${e.runId}${e.timestamp}`),
      );
      setObservations((loaded) =>
        uniqBy([...loaded, ...observations], (e) => `${e.runId}${e.timestamp}`),
      );
      setCursor(asset?.assetMaterializationHistory?.cursor);
    },
    [initialAsOf, beforeParam, assetKey, client, afterParam, params.partitions, params.status],
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
      fetchMore: () => fetch(`${min(all.map((e) => Number(e.timestamp)))}`, cursor),
    };
  }, [materializations, observations, loading, fetch, cursor]);
}
