import {groupBy} from 'lodash';

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
  definedPartitionKeys: string[] | undefined,
): AssetEventGroup[] => {
  const grouped = groupBy(events, (m) => m.partition || NO_PARTITION_KEY);
  const partitionKeys = definedPartitionKeys
    ? [...definedPartitionKeys].reverse()
    : Object.keys(grouped).sort().reverse();

  if (NO_PARTITION_KEY in grouped && definedPartitionKeys) {
    partitionKeys.push(NO_PARTITION_KEY);
  }

  return partitionKeys
    .filter((key) => key !== NO_PARTITION_KEY)
    .map((key) => {
      const sorted = [...(grouped[key] || [])].sort(sortByEventTimestamp);
      const latestMaterialization = sorted.find((a) => a.__typename === 'MaterializationEvent');
      let latest = latestMaterialization || sorted[0] || null;

      if (latest && latest.__typename === 'MaterializationEvent') {
        const observationsAboutLatest = sorted.filter(
          (e) =>
            e.__typename === 'ObservationEvent' && Number(e.timestamp) > Number(latest.timestamp),
        );

        latest = {...latest, metadataEntries: [...latest.metadataEntries]};
        for (const observation of observationsAboutLatest) {
          latest.metadataEntries.push(
            ...observation.metadataEntries.map((e) => ({
              ...e,
              description: `Observed by ${observation.stepKey}${e.description?.length ? ': ' : ''}${
                e.description || ''
              }`,
            })),
          );
        }
      }

      return {
        all: sorted,
        latest: latest,
        timestamp: latest?.timestamp,
        partition: key,
      };
    });
};
