import {PartitionState} from '../partitions/PartitionStatus';

import {
  PartitionHealthData,
  PartitionHealthDimension,
  PartitionHealthDimensionRange,
} from './usePartitionHealthData';

export function isTimeseriesDimension(dimension: PartitionHealthDimension) {
  return isTimeseriesPartition(dimension.partitionKeys[0]);
}
export function isTimeseriesPartition(aPartitionKey = '') {
  return /\d{4}-\d{2}-\d{2}/.test(aPartitionKey); // cheak trick for now
}

export function mergedAssetHealth(
  assetHealth: PartitionHealthData[],
): {
  dimensions: PartitionHealthDimension[];
  stateForKey: (dimensionKeys: string[]) => PartitionState;
  stateForPartialKey: (dimensionKeys: string[]) => PartitionState;
  stateForSingleDimension: (
    dimensionIdx: number,
    dimensionKey: string,
    otherDimensionSelectedKeys?: string[],
  ) => PartitionState;
} {
  if (!assetHealth.length) {
    return {
      dimensions: [],
      stateForKey: () => PartitionState.MISSING,
      stateForPartialKey: () => PartitionState.MISSING,
      stateForSingleDimension: () => PartitionState.MISSING,
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
    stateForPartialKey: (dimensionKeys: string[]) =>
      mergedStates(assetHealth.map((health) => health.stateForPartialKey(dimensionKeys))),
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
  };
}

export function mergedStates(states: PartitionState[]): PartitionState {
  if (states.includes(PartitionState.MISSING) && states.includes(PartitionState.SUCCESS)) {
    return PartitionState.SUCCESS_MISSING;
  } else {
    return states[0];
  }
}

export function explodePartitionKeysInRanges(
  ranges: PartitionHealthDimensionRange[],
  stateForKey: (dimensionKeys: string[]) => PartitionState,
) {
  if (ranges.length === 0) {
    return [];
  }
  if (ranges.length === 1) {
    return ranges[0].selected.map((key) => {
      return {
        partitionKey: key,
        state: stateForKey([key]),
      };
    });
  }
  if (ranges.length === 2) {
    const all: {partitionKey: string; state: PartitionState}[] = [];
    for (const key of ranges[0].selected) {
      for (const subkey of ranges[1].selected) {
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

export const placeholderDimensionRange = (name: string) => ({
  dimension: {name, partitionKeys: []},
  selected: [],
});
