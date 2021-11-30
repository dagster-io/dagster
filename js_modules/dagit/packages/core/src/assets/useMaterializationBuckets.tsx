import * as React from 'react';

import {AssetMaterializationFragment} from './types/AssetMaterializationFragment';

const NO_PARTITION_KEY = '__NO_PARTITION__';

export type HistoricalMaterialization = {
  latest: AssetMaterializationFragment;
  timestamp: string;
  predecessors?: AssetMaterializationFragment[];
};

type Config = {
  materializations: AssetMaterializationFragment[];
  hasPartitions: boolean;
  shouldBucketPartitions: boolean;
};

/**
 * A hook that can bucket a list of materializations by partition, if any, with the `latest`
 * materialization separated from predecessor materializations.
 */
export const useMaterializationBuckets = (config: Config): HistoricalMaterialization[] => {
  const {hasPartitions, materializations, shouldBucketPartitions} = config;
  return React.useMemo(() => {
    if (!hasPartitions || !shouldBucketPartitions) {
      return materializations.map((materialization) => ({
        latest: materialization,
        timestamp: materialization.materializationEvent.timestamp,
      }));
    }

    const buckets: {[key: string]: AssetMaterializationFragment[]} = materializations.reduce(
      (accum, materialization) => {
        const partition = materialization.partition;
        const key = partition || NO_PARTITION_KEY;
        const materializationsForKey = accum[key] || [];
        return {...accum, [key]: [...materializationsForKey, materialization]};
      },
      {},
    );

    const separate = (key: string) => {
      const materializationsForKey = [...buckets[key]].sort(
        (a, b) =>
          Number(b.materializationEvent?.timestamp) - Number(a.materializationEvent?.timestamp),
      );
      const [latest, ...predecessors] = materializationsForKey;
      return {latest, predecessors, timestamp: latest.materializationEvent.timestamp};
    };

    return Object.keys(buckets)
      .sort()
      .reverse()
      .filter((key) => key !== NO_PARTITION_KEY)
      .map(separate)
      .concat(buckets.hasOwnProperty(NO_PARTITION_KEY) ? [separate(NO_PARTITION_KEY)] : []);
  }, [hasPartitions, materializations, shouldBucketPartitions]);
};
