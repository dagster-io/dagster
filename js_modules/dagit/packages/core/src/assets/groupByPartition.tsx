import groupBy from 'lodash/groupBy';
import React from 'react';

import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';
import {AssetObservationFragment} from './types/AssetObservationFragment';

const NO_PARTITION_KEY = '__NO_PARTITION__';

type Event = AssetMaterializationFragment | AssetObservationFragment;

export type AssetEventGroup = {
  latest: Event | null;
  all: Event[];
  timestamp: string;
  partition?: string;
};

const sortByEventTimestamp = (a: Event, b: Event) => Number(b?.timestamp) - Number(a?.timestamp);

/**
 * A hook that can bucket a list of materializations by partition, if any, with the `latest`
 * materialization separated from predecessor materializations.
 */
export const groupByPartition = (
  events: Event[],
  definedPartitionKeys: string[],
): AssetEventGroup[] => {
  const grouped = groupBy(events, (m) => m.partition || NO_PARTITION_KEY);
  const orderedPartitionKeys = [...definedPartitionKeys].reverse();

  if (NO_PARTITION_KEY in grouped) {
    orderedPartitionKeys.push(NO_PARTITION_KEY);
  }

  return orderedPartitionKeys
    .filter((key) => key !== NO_PARTITION_KEY)
    .map((key) => {
      const sorted = [...(grouped[key] || [])].sort(sortByEventTimestamp);
      const latestMaterialization = sorted.find((a) => a.__typename === 'MaterializationEvent');
      const latest = latestMaterialization || sorted[0] || null;

      return {
        all: sorted,
        latest,
        timestamp: latest?.timestamp,
        partition: key,
      };
    });
};

export function useGroupedEvents(
  xAxis: 'partition' | 'time',
  materializations: Event[],
  observations: Event[],
  loadedPartitionKeys: string[] | undefined,
) {
  return React.useMemo<AssetEventGroup[]>(() => {
    const events = [...materializations, ...observations].sort(
      (b, a) => Number(a.timestamp) - Number(b.timestamp),
    );
    if (xAxis === 'partition' && loadedPartitionKeys) {
      return groupByPartition(events, loadedPartitionKeys);
    } else {
      // return a group for every materialization to achieve un-grouped rendering
      return events.map((event) => ({
        latest: event,
        partition: event.partition || undefined,
        timestamp: event.timestamp,
        all: [],
      }));
    }
  }, [loadedPartitionKeys, materializations, observations, xAxis]);
}
