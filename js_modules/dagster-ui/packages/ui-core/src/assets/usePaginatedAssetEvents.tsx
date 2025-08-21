import min from 'lodash/min';
import uniqBy from 'lodash/uniqBy';
import React, {useCallback, useEffect, useMemo, useState} from 'react';

import {AssetKey, AssetViewParams} from './types';
import {
  RecentAssetEventsQuery,
  RecentAssetEventsQueryVariables,
} from './types/useRecentAssetEvents.types';
import {AssetEventFragment, RECENT_ASSET_EVENTS_QUERY} from './useRecentAssetEvents';
import {useApolloClient} from '../apollo-client';
import {AssetEventHistoryEventTypeSelector} from '../graphql/types';
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
    statuses?: AssetEventHistoryEventTypeSelector[];
    partitions?: string[];
  },
) {
  const initialAsOf = params.asOf ? `${Number(params.asOf) + 1}` : undefined;
  const afterParam = params.after ? `${params.after + 1}` : undefined;
  const beforeParam = params.before ? `${params.before - 1}` : undefined;

  const [events, setEvents] = React.useState<AssetEventFragment[]>([]);

  const client = useApolloClient();
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [cursor, setCursor] = useState<string | undefined>(undefined);

  useEffect(() => {
    setEvents([]);
    setCursor(undefined);
  }, [assetKey, params.before, params.after, params.statuses, params.partitions]);

  const fetch = useCallback(
    async (before = initialAsOf ?? beforeParam, cursor: string | undefined = undefined) => {
      if (!assetKey) {
        return;
      }
      if (cursor === '-1') {
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
          partitions: params.partitions,
          eventTypeSelectors: params.statuses ?? [
            AssetEventHistoryEventTypeSelector.MATERIALIZATION,
            AssetEventHistoryEventTypeSelector.OBSERVATION,
            AssetEventHistoryEventTypeSelector.FAILED_TO_MATERIALIZE,
          ],
        },
      });
      setLoading(false);

      const asset = data?.assetOrError.__typename === 'Asset' ? data?.assetOrError : null;

      setLoaded(true);
      setEvents((loaded) =>
        uniqBy(
          [...loaded, ...(asset?.assetEventHistory?.results || [])],
          (e) => `${e.runId}${e.timestamp}.${e.__typename}`,
        ),
      );

      setCursor(asset?.assetEventHistory?.cursor);
    },
    [initialAsOf, beforeParam, assetKey, client, afterParam, params.statuses, params.partitions],
  );

  useBlockTraceUntilTrue('AssetEventsQuery', loaded);

  return useMemo(() => {
    return {
      loading,
      events,
      fetchLatest: fetch,
      fetchMore: () => fetch(`${min(events.map((e) => Number(e.timestamp)))}`, cursor),
    };
  }, [events, loading, fetch, cursor]);
}
