import {gql, useApolloClient} from '@apollo/client';
import isEqual from 'lodash/isEqual';
import React from 'react';

import {assertUnreachable} from '../app/Util';
import {PartitionState} from '../partitions/PartitionStatus';

import {assembleRangesFromTransitions} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {
  PartitionHealthQuery,
  PartitionHealthQueryVariables,
} from './types/usePartitionHealthData.types';

type PartitionHealthMaterializedPartitions = Extract<
  PartitionHealthQuery['assetNodeOrError'],
  {__typename: 'AssetNode'}
>['materializedPartitions'];

/**
 * usePartitionHealthData retrieves partitionKeysByDimension + partitionMaterializationCounts and
 * reshapes the data for rapid retrieval from the UI. The hook exposes a series of getter methods
 * for each asset's data, hiding the underlying data structures from the rest of the app.
 *
 * The hope is that if we want to add support for 3- and 4- dimension partitioned assets, all
 * of the changes will be in this file. The rest of the app already supports N dimensions.
 */

export interface PartitionHealthData {
  assetKey: AssetKey;
  dimensions: PartitionHealthDimension[];

  stateForKey: (dimensionKeys: string[]) => PartitionState;

  ranges: Range[];
  rangesForSingleDimension: (
    dimensionIdx: number,
    otherDimensionSelectedRanges?: PartitionDimensionSelectionRange[] | undefined,
  ) => Range[];
}

export interface PartitionHealthDimension {
  name: string;
  partitionKeys: string[];
}

export type PartitionDimensionSelectionRange = [
  {idx: number; key: string},
  {idx: number; key: string},
];

export type PartitionDimensionSelection = {
  dimension: PartitionHealthDimension;
  selectedKeys: string[];
  selectedRanges: PartitionDimensionSelectionRange[];
};

export function buildPartitionHealthData(data: PartitionHealthQuery, loadKey: AssetKey) {
  const __dims =
    data.assetNodeOrError.__typename === 'AssetNode'
      ? data.assetNodeOrError.partitionKeysByDimension
      : [];

  const materializedPartitions = (data.assetNodeOrError.__typename === 'AssetNode' &&
    data.assetNodeOrError.materializedPartitions) || {
    __typename: 'DefaultPartitions',
    unmaterializedPartitions: [],
    materializedPartitions: [],
  };

  // The backend re-orders the dimensions only for the materializedPartitions ranges so that
  // the time partition is the "primary" one, even if it's dimension[1] elsewhere.
  // This matches the way we display them in the UI and makes some common data retrieval faster,
  // but Dagit's internals always use the REAL ordering of the partition keys, we need to flip
  // everything in this function to match the range data.
  const isRangeDataInverted =
    __dims.length === 2 &&
    materializedPartitions.__typename === 'MultiPartitions' &&
    materializedPartitions.primaryDimensionName !== __dims[0].name;

  const dimensions = isRangeDataInverted ? [__dims[1], __dims[0]] : __dims;
  const ranges = addKeyIndexesToMaterializedRanges(dimensions, materializedPartitions);
  const stateForKey = (dimensionKeys: string[]): PartitionState => {
    return stateForKeyWithRangeOrdering(
      isRangeDataInverted ? dimensionKeys.reverse() : dimensionKeys,
    );
  };

  const stateForKeyWithRangeOrdering = (dimensionKeys: string[]): PartitionState => {
    if (dimensionKeys.length !== dimensions.length) {
      warnUnlessTest('[stateForKey] called with incorrect number of dimensions');
      return PartitionState.MISSING;
    }
    if (dimensionKeys.length === 0) {
      warnUnlessTest('[stateForKey] called with zero dimension keys');
      return PartitionState.MISSING;
    }

    const dIndexes = dimensionKeys.map((key, idx) => dimensions[idx].partitionKeys.indexOf(key));
    const d0Range = ranges.find((r) => r.start.idx <= dIndexes[0] && r.end.idx >= dIndexes[0]);

    if (!d0Range) {
      return PartitionState.MISSING;
    }
    if (!d0Range.subranges || dIndexes.length === 1) {
      return PartitionState.SUCCESS; // 1D case
    }
    const d1Range = d0Range.subranges.find(
      (r) => r.start.idx <= dIndexes[1] && r.end.idx >= dIndexes[1],
    );
    return d1Range ? PartitionState.SUCCESS : PartitionState.MISSING;
  };

  const rangesForSingleDimension = (
    dimensionIdx: number,
    otherDimensionSelectedRanges?: PartitionDimensionSelectionRange[] | undefined,
  ): Range[] => {
    if (dimensions.length === 0) {
      return [];
    }
    if (dimensionIdx >= dimensions.length) {
      warnUnlessTest('[rangesForSingleDimension] called with invalid dimension index');
      return [];
    }

    if (isRangeDataInverted) {
      dimensionIdx = 1 - dimensionIdx;
    }
    if (dimensionIdx === 0 && !otherDimensionSelectedRanges) {
      return removeSubrangesAndJoin(ranges);
    } else if (dimensionIdx === 0 && otherDimensionSelectedRanges) {
      const otherDimensionKeyCount = keyCountInSelection(otherDimensionSelectedRanges);
      if (otherDimensionKeyCount === 0) {
        return [];
      }
      const clipped = ranges
        .map((range) => {
          const subranges = range.subranges
            ? rangesClippedToSelection(range.subranges, otherDimensionSelectedRanges)
            : [];

          return {
            start: range.start,
            end: range.end,
            value: partitionStatusGivenRanges(subranges, otherDimensionKeyCount),
            subranges,
          };
        })
        .filter((range) => range.value !== PartitionState.MISSING) as Range[];
      return removeSubrangesAndJoin(clipped);
    } else {
      const [d0, d1] = dimensions;
      const allKeys = d1.partitionKeys;
      const d0KeyCount = otherDimensionSelectedRanges
        ? keyCountInSelection(otherDimensionSelectedRanges)
        : d0.partitionKeys.length;
      if (d0KeyCount === 0) {
        return [];
      }
      const transitions: {idx: number; delta: number}[] = [];
      const rangesClipped = otherDimensionSelectedRanges
        ? rangesClippedToSelection(ranges, otherDimensionSelectedRanges)
        : ranges;
      for (const range of rangesClipped) {
        const length = range.end.idx - range.start.idx + 1;
        for (const subrange of range.subranges || []) {
          transitions.push({idx: subrange.start.idx, delta: length});
          transitions.push({idx: subrange.end.idx + 1, delta: -length});
        }
      }

      return assembleRangesFromTransitions(allKeys, transitions, d0KeyCount);
    }
  };

  const result: PartitionHealthData = {
    assetKey: loadKey,
    dimensions: __dims.map((d) => ({name: d.name, partitionKeys: d.partitionKeys})),

    stateForKey,

    ranges,
    rangesForSingleDimension,
  };

  return result;
}

// Add indexes to the materializedPartitions data so that we can find specific keys in
// the range structures without having to indexOf the start and end key of every range.
//
export type Range = {
  start: {key: string; idx: number};
  end: {key: string; idx: number};
  value: PartitionState.SUCCESS | PartitionState.SUCCESS_MISSING;
  subranges?: Range[];
};

/** Given a set of materialized ranges and the total number of keys in the dimension,
 * return whether these ranges represent "success" (all the keys), "success_missing"
 * (some of the keys) or "missing". (none of the keys). Used to evaluate the status
 * of the first dimension based on second dimension materialized ranges.
 */
export function partitionStatusGivenRanges(ranges: Range[], totalKeyCount: number) {
  const keyCount = keyCountInRanges(ranges);
  return keyCount === totalKeyCount
    ? PartitionState.SUCCESS
    : keyCount === 0
    ? PartitionState.MISSING
    : PartitionState.SUCCESS_MISSING;
}

/**
 * Given a set of ranges that specify materialized regions and a selection of interest, returns the
 * ranges required to represent the ranges clipped to the selection (within the selected area only.)
 */
export function rangesClippedToSelection(
  ranges: Range[],
  selection: PartitionDimensionSelectionRange[],
) {
  return ranges.flatMap((range) => rangeClippedToSelection(range, selection));
}

/**
 * Given a range eg: [B-F] and a selection of interest [A-C], [D-Z], this function returns the ranges
 * required to represent the range clipped to the selection. ([[B-C], [D-F]])
 */
export function rangeClippedToSelection(
  range: Range,
  selection: PartitionDimensionSelectionRange[],
) {
  const intersecting = selection.filter(
    ([start, end]) => range.start.idx <= end.idx && range.end.idx >= start.idx,
  );
  return intersecting.map(([start, end]) => {
    return {
      value: range.value,
      start: range.start.idx > start.idx ? range.start : start,
      end: range.end.idx < end.idx ? range.end : end,
      subranges: range.subranges,
    };
  });
}

// If you provide the primary dimension ranges of a multi-partitioned asset, there can be tons of
// small ranges which differ only in their subranges, which can lead to tiny "A-B", "C-D", "E"
// ranges rendering when one "A-E" would suffice. This is noticeable because we use a striped pattern
// for partial ranges and the pattern resets.
//
// This function walks the ranges and merges them if their top level status is the same so they
// can be rendered with the minimal number of divs.
//
function removeSubrangesAndJoin(ranges: Range[]): Range[] {
  const result: Range[] = [];
  for (const range of ranges) {
    const last = result[result.length - 1];
    if (last && last.end.idx === range.start.idx - 1 && last.value === range.value) {
      last.end = range.end;
    } else {
      result.push({start: range.start, end: range.end, value: range.value});
    }
  }
  return result;
}

// In a follow-up, maybe we make these two data structures share a signature

export function keyCountInRanges(ranges: Range[]) {
  let count = 0;
  for (const range of ranges) {
    count += range.end.idx - range.start.idx + 1;
  }
  return count;
}
export function keyCountInSelection(selections: PartitionDimensionSelectionRange[]) {
  let count = 0;
  for (const [start, end] of selections) {
    count += end.idx - start.idx + 1;
  }
  return count;
}

// Take the health data of an asset and the user's selection on each
// dimension, and return the number of keys of each state within that
// set of the partition keys.
//
export function keyCountByStateInSelection(
  assetHealth: PartitionHealthData,
  selections: PartitionDimensionSelection[],
) {
  if (selections.length === 0) {
    warnUnlessTest('[keyCountByStateInSelection] A selection must be provided for dimension 0.');
    return {
      [PartitionState.MISSING]: 0,
      [PartitionState.SUCCESS]: 0,
    };
  }

  const total = selections
    .map((s) => keyCountInSelection(s.selectedRanges))
    .reduce((a, b) => (a ? a * b : b), 0);

  const rangesInSelection = rangesClippedToSelection(
    assetHealth?.ranges || [],
    selections[0].selectedRanges,
  );
  const secondDimensionKeyCount =
    selections.length > 1 ? keyCountInSelection(selections[1].selectedRanges) : 1;

  const success = rangesInSelection.reduce(
    (a, b) =>
      a +
      (b.end.idx - b.start.idx + 1) *
        (b.subranges
          ? keyCountInRanges(rangesClippedToSelection(b.subranges, selections[1].selectedRanges))
          : secondDimensionKeyCount),
    0,
  );

  return {
    [PartitionState.MISSING]: total - success,
    [PartitionState.SUCCESS]: success,
  };
}

// Given a set of ranges representing materialization status across the key space,
// find the range containing the given key and reutnr it's state, or MISSING.
//
export function partitionStateAtIndex(ranges: Range[], idx: number) {
  return (
    ranges.find((r) => r.start.idx <= idx && r.end.idx >= idx)?.value || PartitionState.MISSING
  );
}

function addKeyIndexesToMaterializedRanges(
  dimensions: {name: string; partitionKeys: string[]}[],
  materializedPartitions: PartitionHealthMaterializedPartitions,
) {
  const result: Range[] = [];
  if (dimensions.length === 0) {
    return result;
  }
  if (materializedPartitions.__typename === 'DefaultPartitions') {
    const dim = dimensions[0];
    return rangesForKeys(materializedPartitions.materializedPartitions, dim.partitionKeys);
  }

  for (const range of materializedPartitions.ranges) {
    if (range.__typename === 'TimePartitionRange') {
      result.push({
        value: PartitionState.SUCCESS,
        start: {key: range.startKey, idx: dimensions[0].partitionKeys.indexOf(range.startKey)},
        end: {key: range.endKey, idx: dimensions[0].partitionKeys.indexOf(range.endKey)},
      });
    } else if (range.__typename === 'MaterializedPartitionRange2D') {
      if (dimensions.length !== 2) {
        warnUnlessTest('[addKeyIndexesToMaterializedRanges] Found 2D health data for 1D asset');
        return result;
      }
      const [dim0, dim1] = dimensions;
      const subranges: Range[] = addKeyIndexesToMaterializedRanges([dim1], range.secondaryDim);
      const subrangeIsAll = rangesCoverAll(subranges, dim1.partitionKeys.length);

      result.push({
        value: subrangeIsAll ? PartitionState.SUCCESS : PartitionState.SUCCESS_MISSING,
        subranges,
        start: {
          key: range.primaryDimStartKey,
          idx: dim0.partitionKeys.indexOf(range.primaryDimStartKey),
        },
        end: {
          key: range.primaryDimEndKey,
          idx: dim0.partitionKeys.indexOf(range.primaryDimEndKey),
        },
      });
    } else {
      assertUnreachable(range);
    }
  }

  return result;
}

export function rangesForKeys(keys: string[], allKeys: string[]): Range[] {
  if (keys.length === 0 || allKeys.length === 0) {
    return [];
  }

  // If you gave us two arrays of equal length, we don't need to iterate - this is the entire range
  if (keys.length === allKeys.length) {
    return [
      {
        start: {key: allKeys[0], idx: 0},
        end: {key: allKeys[allKeys.length - 1], idx: allKeys.length - 1},
        value: PartitionState.SUCCESS as const,
      },
    ];
  }

  // Ok - we want to convert keys=[A,B,C,F] in allKeys=[A,B,C,D,E,F,G], into ranges. We could do the "bad"
  // thing and give you a separate range for every key, but this has downstream implications (like creating
  // one <div /> for every key in <PartitionHealthSummary />). Instead, we do index lookups on keys, sort
  // them, and then walk the sorted list assembling them into ranges when they're contiguous.
  const keysIdxs = keys.map((k) => allKeys.indexOf(k)).sort((a, b) => a - b);
  const ranges: Range[] = [];

  for (const idx of keysIdxs) {
    if (ranges.length && idx === ranges[ranges.length - 1].end.idx + 1) {
      ranges[ranges.length - 1].end = {idx, key: allKeys[idx]};
    } else {
      ranges.push({
        start: {idx, key: allKeys[idx]},
        end: {idx, key: allKeys[idx]},
        value: PartitionState.SUCCESS,
      });
    }
  }

  return ranges;
}

// Returns true if the provided ranges span keyCount keys, indicating that they cover the entire key space.
//
function rangesCoverAll(ranges: Range[], keyCount: number) {
  let last = 0;
  for (const range of ranges) {
    if (range.start.idx !== last) {
      return false;
    }
    last = range.end.idx + 1;
  }
  return last === keyCount;
}

// Note: assetLastMaterializedAt is used as a "hint" - if the input value changes, it's
// a sign that we should invalidate and reload previously loaded health stats. We don't
// clear them immediately to avoid an empty state.
//
export function usePartitionHealthData(assetKeys: AssetKey[], assetLastMaterializedAt = '') {
  const [result, setResult] = React.useState<(PartitionHealthData & {fetchedAt: string})[]>([]);
  const client = useApolloClient();

  const assetKeyJSONs = assetKeys.map((k) => JSON.stringify(k));
  const assetKeyJSON = JSON.stringify(assetKeyJSONs);
  const missingKeyJSON = assetKeyJSONs.find(
    (k) =>
      !result.some(
        (r) => JSON.stringify(r.assetKey) === k && r.fetchedAt === assetLastMaterializedAt,
      ),
  );

  React.useMemo(() => {
    if (!missingKeyJSON) {
      return;
    }
    const loadKey: AssetKey = JSON.parse(missingKeyJSON);
    const run = async () => {
      const {data} = await client.query<PartitionHealthQuery, PartitionHealthQueryVariables>({
        query: PARTITION_HEALTH_QUERY,
        fetchPolicy: 'network-only',
        variables: {
          assetKey: {path: loadKey.path},
        },
      });
      const loaded = buildPartitionHealthData(data, loadKey);
      setResult((result) => [
        ...result.filter((r) => !isEqual(r.assetKey, loadKey)),
        {...loaded, fetchedAt: assetLastMaterializedAt},
      ]);
    };
    run();
  }, [client, missingKeyJSON, assetLastMaterializedAt]);

  return React.useMemo(() => {
    const assetKeyJSONs = JSON.parse(assetKeyJSON);
    return result.filter((r) => assetKeyJSONs.includes(JSON.stringify(r.assetKey)));
  }, [assetKeyJSON, result]);
}

export const PARTITION_HEALTH_QUERY = gql`
  query PartitionHealthQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        partitionKeysByDimension {
          name
          partitionKeys
        }
        materializedPartitions {
          ... on TimePartitions {
            ranges {
              startTime
              endTime
              startKey
              endKey
            }
          }
          ... on DefaultPartitions {
            materializedPartitions
          }
          ... on MultiPartitions {
            primaryDimensionName
            ranges {
              primaryDimStartKey
              primaryDimEndKey
              primaryDimStartTime
              primaryDimEndTime
              secondaryDim {
                ... on TimePartitions {
                  ranges {
                    startTime
                    endTime
                    startKey
                    endKey
                  }
                }
                ... on DefaultPartitions {
                  materializedPartitions
                }
              }
            }
          }
        }
      }
    }
  }
`;
function warnUnlessTest(msg: string) {
  if (process.env.NODE_ENV !== 'test') {
    console.warn(msg);
  }
}
