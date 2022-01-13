import {groupBy} from 'lodash';

import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';

const NO_PARTITION_KEY = '__NO_PARTITION__';

export type MaterializationGroup = {
  latest: AssetMaterializationFragment | null;
  predecessors: AssetMaterializationFragment[];
  timestamp: string;
  partition?: string;
};

const sortByEventTimestamp = (a: AssetMaterializationFragment, b: AssetMaterializationFragment) =>
  Number(b.materializationEvent?.timestamp) - Number(a.materializationEvent?.timestamp);

/**
 * A hook that can bucket a list of materializations by partition, if any, with the `latest`
 * materialization separated from predecessor materializations.
 */
export const groupByPartition = (
  materializations: AssetMaterializationFragment[],
  definedPartitionKeys: string[] | undefined,
): MaterializationGroup[] => {
  const grouped = groupBy(materializations, (m) => m.partition || NO_PARTITION_KEY);
  const partitionKeys = definedPartitionKeys
    ? [...definedPartitionKeys].reverse()
    : Object.keys(grouped).sort().reverse();

  if (NO_PARTITION_KEY in grouped && definedPartitionKeys) {
    partitionKeys.push(NO_PARTITION_KEY);
  }

  return partitionKeys
    .filter((key) => key !== NO_PARTITION_KEY)
    .map((key) => {
      const [latest, ...predecessors] = [...(grouped[key] || [])].sort(sortByEventTimestamp);
      return {
        predecessors,
        latest: latest || null,
        timestamp: latest?.materializationEvent.timestamp,
        partition: key,
      };
    });
};
