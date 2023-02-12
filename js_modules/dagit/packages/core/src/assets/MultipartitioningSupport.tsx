import {PartitionState} from '../partitions/PartitionStatus';

import {
  PartitionHealthData,
  PartitionHealthDimension,
  PartitionDimensionSelection,
  Range,
} from './usePartitionHealthData';

export function isTimeseriesDimension(dimension: PartitionHealthDimension) {
  return isTimeseriesPartition(dimension.partitionKeys[0]);
}
export function isTimeseriesPartition(aPartitionKey = '') {
  return /\d{4}-\d{2}-\d{2}/.test(aPartitionKey); // cheak trick for now
}

export function mergedAssetHealth(
  assetHealth: PartitionHealthData[],
): Omit<PartitionHealthData, 'assetKey'> {
  if (!assetHealth.length) {
    return {
      dimensions: [],
      stateForKey: () => PartitionState.MISSING,
      stateForSingleDimension: () => PartitionState.MISSING,
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
    })),
    stateForKey: (dimensionKeys: string[]) =>
      mergedStates(assetHealth.map((health) => health.stateForKey(dimensionKeys))),
    stateForSingleDimension: (
      dimensionIdx: number,
      dimensionKey: string,
      otherDimensionSelectedKeys?: string[],
    ) =>
      mergedStates(
        assetHealth.map((health) =>
          health.stateForSingleDimension(dimensionIdx, dimensionKey, otherDimensionSelectedKeys),
        ),
      ),
    rangesForSingleDimension: (dimensionIdx, otherDimensionSelectedRanges?) =>
      mergedRanges(
        assetHealth.map((health) =>
          health.rangesForSingleDimension(dimensionIdx, otherDimensionSelectedRanges),
        ),
      ),
  };
}

export function mergedStates(states: PartitionState[]): PartitionState {
  if (states.includes(PartitionState.MISSING) && states.includes(PartitionState.SUCCESS)) {
    return PartitionState.SUCCESS_MISSING;
  } else {
    return states[0];
  }
}

/**
 * This function takes the materialized ranges of several assets and returns a single set of ranges with the
 * "success" / "partial" (SUCCESS_MISSING) states have been flattened together. This implementation is based
 * on this solution: https://stackoverflow.com/questions/4542892 and involves placing all the start/end points
 * into an ordered array.
 *
 * Why?: If you select multiple assets with the same partitioning in the asset graph and click Materialize,
 * the asset health bar you see is a flattened representation of the health of all of all of them, with a
 * "show per-asset health" button beneath.
 *
 * Note that this function does not populate subranges on the returned ranges -- if you want to filter the
 * health data to a second-dimension partition key range, do that FIRST and then merge the results.
 */
export function mergedRanges(rangeSets: Range[][]): Range[] {
  const transitions: {key: string; idx: number; delta: 1 | -1}[] = [];
  for (const ranges of rangeSets) {
    for (const range of ranges) {
      transitions.push({key: range.start.key, idx: range.start.idx, delta: 1});
      transitions.push({key: range.end.key, idx: range.end.idx, delta: -1});
    }
  }

  // sort the array
  transitions.sort((a, b) => a.idx - b.idx);

  // walk the transitions array and apply the transitions to a counter, creating an array of just the changes
  // in the number of currently-overlapping ranges. (eg: how many of the assets are materialized at this time).
  //
  // FROM: [{idx: 0, delta: 1}, {idx: 0, delta: 1}, {idx: 3, delta: 1}, {idx: 10, delta: -1}]
  //   TO: [{idx: 0, depth: 2}, {idx: 3, depth: 3}, {idx: 10, depth: 2}]
  //
  const depths: {idx: number; key: string; depth: number}[] = [];
  for (const transition of transitions) {
    const last = depths[depths.length - 1];
    if (last && last.idx === transition.idx) {
      last.depth += transition.delta;
    } else {
      depths.push({
        idx: transition.idx,
        key: transition.key,
        depth: (last?.depth || 0) + transition.delta,
      });
    }
  }

  // Ok! This array of depth values IS our SUCCESS vs. SUCCESS_MISSING range state. We just need to flatten it one
  // more time. Anytime depth == rangeSets.length - 1, all the assets were materialzied within this band.
  const result: Range[] = [];
  for (const {idx, key, depth} of depths) {
    const value =
      depth === rangeSets.length - 1
        ? PartitionState.SUCCESS
        : depth > 0
        ? PartitionState.SUCCESS_MISSING
        : PartitionState.MISSING;

    const last = result[result.length - 1];
    if (last && last.value !== value) {
      last.end = {idx, key};
    }
    if (value !== PartitionState.MISSING && last?.value !== value) {
      result.push({
        start: {idx, key},
        end: {idx, key},
        value,
      });
    }
  }

  return result;
}

export function explodePartitionKeysInSelection(
  selections: PartitionDimensionSelection[],
  stateForKey: (dimensionKeys: string[]) => PartitionState,
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
    const all: {partitionKey: string; state: PartitionState}[] = [];
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
  dimension: {name, partitionKeys: []},
  selectedKeys: [],
  selectedRanges: [],
});
