import isEqual from 'lodash/isEqual';
import uniq from 'lodash/uniq';

import {PartitionDefinitionType} from '../graphql/types';

import {AssetPartitionStatus, emptyAssetPartitionStatusCounts} from './AssetPartitionStatus';
import {
  PartitionHealthData,
  PartitionHealthDimension,
  PartitionDimensionSelection,
  Range,
  PartitionHealthDataMerged,
} from './usePartitionHealthData';

export function isTimeseriesDimension(dimension: PartitionHealthDimension) {
  return isTimeseriesPartition(dimension.partitionKeys[0]);
}
export function isTimeseriesPartition(aPartitionKey = '') {
  return /\d{4}-\d{2}-\d{2}/.test(aPartitionKey); // cheak trick for now
}

/*
This function takes the health of several assets and returns a single health object in which SUCCESS
means that all the assets were in a SUCCESS state for that partition and SUCCESS_MISSING means only
some were - or that the assets were individually in SUCCESS_MISSING state. (multipartitioned only)

This representation is somewhat "lossy" because an individual asset can also be in SUCCESS_MISSING
state for a partition key if it is multi-dimensional.

Note: For this to work, all of the assets must share the same partition dimensions. This function
throws exceptions if that is not the case.

Q: Why do we do this at all?
A: If you select multiple assets with the same partitioning in the asset graph and click Materialize,
the asset health bar you see is a flattened representation of the health of all of all of them, with a
"show per-asset health" button beneath.

*/
export function mergedAssetHealth(assetHealth: PartitionHealthData[]): PartitionHealthDataMerged {
  if (!assetHealth.length) {
    return {
      dimensions: [],
      stateForKey: () => [AssetPartitionStatus.MISSING],
      rangesForSingleDimension: () => [],
    };
  }

  const dimensions = assetHealth[0].dimensions;

  if (!assetHealth.every((h) => h.dimensions.length === dimensions.length)) {
    throw new Error('Attempting to show unified asset health for assets with different dimensions');
  }

  if (
    !assetHealth.every((h) =>
      h.dimensions.every(
        (dim, idx) => dim.partitionKeys.length === dimensions[idx].partitionKeys.length,
      ),
    )
  ) {
    throw new Error(
      'Attempting to show unified asset health for assets with dimension of different lengths',
    );
  }

  return {
    dimensions: dimensions.map((dimension) => ({
      name: dimension.name,
      partitionKeys: dimension.partitionKeys,
      type: dimension.type,
    })),
    stateForKey: (dimensionKeys: string[]) =>
      uniq(assetHealth.map((health) => health.stateForKey(dimensionKeys))),
    rangesForSingleDimension: (dimensionIdx, otherDimensionSelectedRanges?) =>
      mergedRanges(
        dimensions[dimensionIdx].partitionKeys,
        assetHealth.map((health) =>
          health.rangesForSingleDimension(dimensionIdx, otherDimensionSelectedRanges),
        ),
      ),
  };
}

/**
 * This function takes the materialized ranges of several assets and returns a single set of ranges with
 * the "success" / "partial" (SUCCESS_MISSING) states flattened as described above. This implementation
 * is based on https://stackoverflow.com/questions/4542892 and involves placing all the start/end points
 * into an ordered array and then walking an "accumulator" over the points. If the accumulator's counter is
 * incremented to the total number of assets at any point, they are all materialized.
 *
 * Note that this function does not populate subranges on the returned ranges -- if you want to filter the
 * health data to a second-dimension partition key selection, do that FIRST and then merge the results.
 *
 * This algorithm only works because asset state is a boolean -- if we add a third state like "stale"
 * to the individual range representation, this might get more complicated.
 *
 * Q: Why does this require the dimension keys?
 * A: Right now, partition health ranges are inclusive - {start: b, end: d} is "B through D". If "B" is
 * where a new range begins and we need to switch from "partial" to "success", we need to end the previous
 * range at "B - 1", and we may not have any range in the input we can reference to get that value.
 */
export function mergedRanges(allKeys: string[], rangeSets: Range[][]): Range[] {
  if (rangeSets.length === 1) {
    return rangeSets[0];
  }

  const transitions: Transition[] = [];
  for (const ranges of rangeSets) {
    for (const range of ranges) {
      transitions.push({idx: range.start.idx, delta: 1, state: range.value});
      transitions.push({idx: range.end.idx + 1, delta: -1, state: range.value});
    }
  }

  return assembleRangesFromTransitions(allKeys, transitions, rangeSets.length);
}

export type Transition = {idx: number; delta: number; state: AssetPartitionStatus[]};

export function assembleRangesFromTransitions(
  allKeys: string[],
  transitionsUnsorted: Transition[],
  maxOverlap: number,
) {
  // sort the input array, this algorithm does not work unless the transitions are in order
  const transitions = [...transitionsUnsorted].sort((a, b) => a.idx - b.idx || b.delta - a.delta);

  // walk the transitions array and apply the transitions to a counter, creating an array of just the changes
  // in the number of currently-overlapping ranges. (eg: how many of the assets are materialized at this time).
  //
  // FROM: [{idx: 0, delta: 1}, {idx: 0, delta: 1}, {idx: 3, delta: 1}, {idx: 10, delta: -1}]
  //   TO: [{idx: 0, depth: 2}, {idx: 3, depth: 3}, {idx: 10, depth: 2}]
  //
  const depths: {
    idx: number;
    [AssetPartitionStatus.FAILED]: number;
    [AssetPartitionStatus.MATERIALIZING]: number;
    [AssetPartitionStatus.MATERIALIZED]: number;
    [AssetPartitionStatus.MISSING]: number;
  }[] = [];
  for (const transition of transitions) {
    for (const state of transition.state) {
      const last = depths[depths.length - 1];
      if (last && last.idx === transition.idx) {
        last[state] = (last[state] || 0) + transition.delta;
      } else {
        depths.push({
          ...(last || emptyAssetPartitionStatusCounts()),
          [state]: (last?.[state] || 0) + transition.delta,
          idx: transition.idx,
        });
      }
    }
  }

  // Ok! This array of depth values IS our SUCCESS vs. SUCCESS_MISSING range state. We just need to flatten it one
  // more time. Anytime depth == rangeSets.length - 1, all the assets were materialzied within this band.
  //
  const result: Range[] = [];

  for (const {idx, MATERIALIZED, FAILED, MATERIALIZING, MISSING} of depths) {
    const value: AssetPartitionStatus[] = [];
    if (FAILED > 0) {
      value.push(AssetPartitionStatus.FAILED);
    }
    if (MATERIALIZED > 0) {
      value.push(AssetPartitionStatus.MATERIALIZED);
    }
    if (MATERIALIZING > 0) {
      value.push(AssetPartitionStatus.MATERIALIZING);
    }
    if (MISSING > 0 || FAILED + MATERIALIZED + MATERIALIZING < maxOverlap) {
      value.push(AssetPartitionStatus.MISSING);
    }

    const last = result[result.length - 1];

    if (!isEqual(last?.value, value)) {
      if (last) {
        last.end = {idx: idx - 1, key: allKeys[idx - 1]};
      }
      result.push({start: {idx, key: allKeys[idx]}, end: {idx, key: allKeys[idx]}, value});
    }
  }
  return result.filter(
    (range) =>
      range.start.idx < allKeys.length && !isEqual(range.value, [AssetPartitionStatus.MISSING]),
  );
}

export function partitionDefinitionsEqual(
  a: {description: string; dimensionTypes: {name: string}[]},
  b: {description: string; dimensionTypes: {name: string}[]},
) {
  return (
    a.description === b.description &&
    JSON.stringify(a.dimensionTypes) === JSON.stringify(b.dimensionTypes)
  );
}

export function explodePartitionKeysInSelection(
  selections: PartitionDimensionSelection[],
  stateForKey: (dimensionKeys: string[]) => AssetPartitionStatus[],
) {
  if (selections.length === 0) {
    return [];
  }
  if (selections.length === 1) {
    return selections[0].selectedKeys.map((key) => {
      return {
        partitionKey: key,
        state: stateForKey([key]),
      };
    });
  }
  if (selections.length === 2) {
    const all: {partitionKey: string; state: AssetPartitionStatus[]}[] = [];
    for (const key of selections[0].selectedKeys) {
      for (const subkey of selections[1].selectedKeys) {
        all.push({
          partitionKey: `${key}|${subkey}`,
          state: stateForKey([key, subkey]),
        });
      }
    }
    return all;
  }

  throw new Error('Unsupported >2 partitions defined');
}

export const placeholderDimensionSelection = (name: string): PartitionDimensionSelection => ({
  dimension: {name, partitionKeys: [], type: PartitionDefinitionType.STATIC},
  selectedKeys: [],
  selectedRanges: [],
});
