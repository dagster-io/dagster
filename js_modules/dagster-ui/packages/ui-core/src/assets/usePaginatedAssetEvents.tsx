import min from 'lodash/min';
import uniqBy from 'lodash/uniqBy';
import React, {useCallback, useEffect, useMemo, useState} from 'react';

import {clipEventsToSharedMinimumTime} from './clipEventsToSharedMinimumTime';
import {AssetKey, AssetViewParams} from './types';
import {
  AssetObservationFragment,
  RecentAssetEventsQuery,
  RecentAssetEventsQueryVariables,
} from './types/useRecentAssetEvents.types';
import {AssetMaterializationFragment, RECENT_ASSET_EVENTS_QUERY} from './useRecentAssetEvents';
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
  }, [assetKey, params.before, params.after, params.status]);

  const fetch = useCallback(
    async (before = initialAsOf ?? beforeParam, cursor: string | undefined = undefined) => {
      if (!assetKey) {
        return;
      }
      setLoading(true);
      const {data} = await client.query<RecentAssetEventsQuery, RecentAssetEventsQueryVariables>({
        query: RECENT_ASSET_EVENTS_QUERY,
        variables: {
          assetKey: {path: assetKey.path},
          limit: 100,
          cursor,
          before,
          after: afterParam,
          eventTypeSelector: params.status ?? MaterializationHistoryEventTypeSelector.ALL,
        },
      });
      setLoading(false);

      const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;

      const {materializations, observations} = clipEventsToSharedMinimumTime(
        asset?.assetMaterializationHistory?.results || [],
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
      setCursor(asset?.assetMaterializationHistory?.cursor);
    },
    [initialAsOf, beforeParam, assetKey, client, afterParam, params.status],
  );

  useBlockTraceUntilTrue('AssetEventsQuery', loaded);

  return useMemo(() => {
    const all = [...materializations, ...observations];

    return {
      loading,
      materializations,
      observations,
      fetchLatest: fetch,
      fetchMore: () => fetch(`${min(all.map((e) => Number(e.timestamp)))}`, cursor),
    };
  }, [materializations, observations, loading, fetch, cursor]);
}
