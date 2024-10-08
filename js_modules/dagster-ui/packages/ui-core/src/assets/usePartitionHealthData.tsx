import isEqual from 'lodash/isEqual';
import keyBy from 'lodash/keyBy';
import {useEffect, useMemo, useState} from 'react';

import {AssetPartitionStatus, emptyAssetPartitionStatusCounts} from './AssetPartitionStatus';
import {Transition, assembleRangesFromTransitions} from './MultipartitioningSupport';
import {usePartitionDataSubscriber} from './PartitionSubscribers';
import {AssetKey} from './types';
import {
  PartitionHealthQuery,
  PartitionHealthQueryVariables,
} from './types/usePartitionHealthData.types';
import {gql, useApolloClient} from '../apollo-client';
import {assertUnreachable} from '../app/Util';
import {LiveDataForNode} from '../asset-graph/Utils';
import {PartitionDefinitionType, PartitionRangeStatus} from '../graphql/types';
import {assembleIntoSpans} from '../partitions/SpanRepresentation';
import {useBlockTraceUntilTrue} from '../performance/TraceContext';

type PartitionHealthMaterializedPartitions = Extract<
  PartitionHealthQuery['assetNodeOrError'],
  {__typename: 'AssetNode'}
>['assetPartitionStatuses'];

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

  stateForKey: (dimensionKeys: string[]) => AssetPartitionStatus;
  stateForKeyIdx: (dimenstionIdxs: number[]) => AssetPartitionStatus;

  ranges: Range[];
  isRangeDataInverted: boolean;
  rangesForSingleDimension: (
    dimensionIdx: number,
    otherDimensionSelectedRanges?: PartitionDimensionSelectionRange[] | undefined,
  ) => Range[];
}

export interface PartitionHealthDataMerged {
  dimensions: PartitionHealthDimension[];

  stateForKey: (dimensionKeys: string[]) => AssetPartitionStatus[];
  stateForKeyIdx: (dimenstionIdxs: number[]) => AssetPartitionStatus[];

  rangesForSingleDimension: (
    dimensionIdx: number,
    otherDimensionSelectedRanges?: PartitionDimensionSelectionRange[] | undefined,
  ) => Range[];
}

export interface PartitionHealthDimension {
  name: string;
  type: PartitionDefinitionType;
  partitionKeys: string[];
}

export type PartitionDimensionSelectionRange = Pick<Range, 'start' | 'end'>;

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

  const assetPartitionStatuses = (data.assetNodeOrError.__typename === 'AssetNode' &&
    data.assetNodeOrError.assetPartitionStatuses) || {
    __typename: 'DefaultPartitionStatuses',
    unmaterializedPartitions: [],
    materializedPartitions: [],
    materializingPartitions: [],
    failedPartitions: [],
  };

  // The backend re-orders the dimensions only for the materializedPartitions ranges so that
  // the time partition is the "primary" one, even if it's dimension[1] elsewhere.
  // This matches the way we display them in the UI and makes some common data retrieval faster,
  // but Dagster's internals always use the REAL ordering of the partition keys, we need to flip
  // everything in this function to match the range data.
  const isRangeDataInverted =
    __dims.length === 2 &&
    assetPartitionStatuses.__typename === 'MultiPartitionStatuses' &&
    assetPartitionStatuses.primaryDimensionName !== __dims[0]!.name;

  const dimensions = isRangeDataInverted ? [__dims[1]!, __dims[0]!] : __dims;
  const ranges = addKeyIndexesToMaterializedRanges(dimensions, assetPartitionStatuses);

  const stateForKey = (dimensionKeys: string[]): AssetPartitionStatus => {
    if (dimensionKeys.length !== __dims.length) {
      warnUnlessTest('[stateForKey] called with incorrect number of dimensions');
      return AssetPartitionStatus.MISSING;
    }
    if (dimensionKeys.length === 0) {
      warnUnlessTest('[stateForKey] called with zero dimension keys');
      return AssetPartitionStatus.MISSING;
    }
    return stateForKeyIdx(dimensionKeys.map((key, idx) => __dims[idx]!.partitionKeys.indexOf(key)));
  };

  const stateForKeyIdx = (dIndexes: number[]): AssetPartitionStatus => {
    return stateForKeyIdxWithRangeOrdering(isRangeDataInverted ? dIndexes.reverse() : dIndexes);
  };

  const stateForKeyIdxWithRangeOrdering = (dIndexes: number[]): AssetPartitionStatus => {
    if (dIndexes.length !== dimensions.length) {
      warnUnlessTest('[stateForKey] called with incorrect number of dimensions');
      return AssetPartitionStatus.MISSING;
    }
    if (dIndexes.length === 0) {
      warnUnlessTest('[stateForKey] called with zero dimension keys');
      return AssetPartitionStatus.MISSING;
    }

    const d0Range = ranges.find((r) => r.start.idx <= dIndexes[0]! && r.end.idx >= dIndexes[0]!);

    if (!d0Range) {
      return AssetPartitionStatus.MISSING;
    }
    if (!d0Range.subranges || dIndexes.length === 1) {
      return d0Range.value[0]!; // 1D case
    }
    const d1Range = d0Range.subranges.find(
      (r) => r.start.idx <= dIndexes[1]! && r.end.idx >= dIndexes[1]!,
    );
    return d1Range ? d1Range.value[0]! : AssetPartitionStatus.MISSING;
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
      const otherDimensionKeyCount = keyCountInRanges(otherDimensionSelectedRanges);
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
        .filter((range) => !isEqual(range.value, [AssetPartitionStatus.MISSING])) as Range[];
      return removeSubrangesAndJoin(clipped);
    } else {
      const [d0, d1] = dimensions;
      const allKeys = d1!.partitionKeys;
      const d0KeyCount = otherDimensionSelectedRanges
        ? keyCountInRanges(otherDimensionSelectedRanges)
        : d0!.partitionKeys.length;
      if (d0KeyCount === 0) {
        return [];
      }
      const transitions: Transition[] = [];
      const rangesClipped = otherDimensionSelectedRanges
        ? rangesClippedToSelection(ranges, otherDimensionSelectedRanges)
        : ranges;
      for (const range of rangesClipped) {
        const length = range.end.idx - range.start.idx + 1;
        for (const subrange of range.subranges || []) {
          transitions.push({idx: subrange.start.idx, delta: length, state: subrange.value});
          transitions.push({idx: subrange.end.idx + 1, delta: -length, state: subrange.value});
        }
      }

      return assembleRangesFromTransitions(allKeys, transitions, d0KeyCount);
    }
  };

  const result: PartitionHealthData = {
    assetKey: loadKey,
    dimensions: __dims.map((d) => ({name: d.name, partitionKeys: d.partitionKeys, type: d.type})),

    stateForKey,
    stateForKeyIdx,

    ranges,
    rangesForSingleDimension,
    isRangeDataInverted,
  };

  return result;
}

// Add indexes to the materializedPartitions data so that we can find specific keys in
// the range structures without having to indexOf the start and end key of every range.
//
export type Range = {
  start: {key: string; idx: number};
  end: {key: string; idx: number};
  value: AssetPartitionStatus[];
  subranges?: Range[];
};

/** Given a set of materialized ranges and the total number of keys in the dimension,
 * return whether these ranges represent "success" (all the keys), "success_missing"
 * (some of the keys) or "missing". (none of the keys). Used to evaluate the status
 * of the first dimension based on second dimension materialized ranges.
 */
export function partitionStatusGivenRanges(
  ranges: Range[],
  totalKeyCount: number,
): AssetPartitionStatus[] {
  const materializedCount = keyCountInRanges(
    ranges.filter((r) => r.value.includes(AssetPartitionStatus.MATERIALIZED)),
  );
  const materializingCount = keyCountInRanges(
    ranges.filter((r) => r.value.includes(AssetPartitionStatus.MATERIALIZING)),
  );
  const failedCount = keyCountInRanges(
    ranges.filter((r) => r.value.includes(AssetPartitionStatus.FAILED)),
  );
  const statuses: AssetPartitionStatus[] = [];
  if (materializedCount > 0) {
    statuses.push(AssetPartitionStatus.MATERIALIZED);
  }
  if (materializingCount > 0) {
    statuses.push(AssetPartitionStatus.MATERIALIZING);
  }
  if (failedCount > 0) {
    statuses.push(AssetPartitionStatus.FAILED);
  }
  if (materializedCount + failedCount + materializingCount < totalKeyCount) {
    statuses.push(AssetPartitionStatus.MISSING);
  }
  return statuses;
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
    ({start, end}) => range.start.idx <= end.idx && range.end.idx >= start.idx,
  );
  return intersecting.map(({start, end}) => {
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
    if (last && last.end.idx === range.start.idx - 1 && isEqual(last.value, range.value)) {
      last.end = range.end;
    } else {
      result.push({start: range.start, end: range.end, value: range.value});
    }
  }
  return result;
}

export function selectionRangeWithSingleKey(
  key: string,
  dim: PartitionHealthDimension,
): PartitionDimensionSelectionRange {
  const idx = dim.partitionKeys.indexOf(key);
  return {start: {key, idx}, end: {key, idx}};
}

// In a follow-up, maybe we make these two data structures share a signature

export function keyCountInRanges(ranges: Range[] | PartitionDimensionSelectionRange[]) {
  let count = 0;
  for (const range of ranges) {
    count += range.end.idx - range.start.idx + 1;
  }
  return count;
}

export function keyCountInSelections(selections: PartitionDimensionSelection[]) {
  return selections
    .map((s) => keyCountInRanges(s.selectedRanges))
    .reduce((a, b) => (a ? a * b : b), 0);
}

// Take the health data of an asset and the user's selection on each
// dimension, and return the number of keys of each state within that
// set of the partition keys.
//
export function keyCountByStateInSelection(
  assetHealth: PartitionHealthData,
  _selections: PartitionDimensionSelection[],
) {
  if (_selections.length === 0) {
    warnUnlessTest('[keyCountByStateInSelection] A selection must be provided for dimension 0.');
    return emptyAssetPartitionStatusCounts();
  }

  // Make sure that the provided selections are in the same order as the /underlying/
  // range data, which may be reversed if the time series is the second axis.
  const selections = assetHealth?.isRangeDataInverted ? [..._selections].reverse() : _selections;
  const total = keyCountInSelections(selections);

  const rangesInSelection = rangesClippedToSelection(
    assetHealth?.ranges || [],
    selections[0]!.selectedRanges,
  );

  const secondDimensionKeyCount =
    selections.length > 1 ? keyCountInRanges(selections[1]!.selectedRanges) : 1;

  const sumWithStatus = (status: AssetPartitionStatus) => {
    return rangesInSelection.reduce(
      (a, b) =>
        a +
        (b.end.idx - b.start.idx + 1) *
          (b.subranges
            ? keyCountInRanges(
                rangesClippedToSelection(b.subranges, selections[1]!.selectedRanges).filter((b) =>
                  b.value.includes(status),
                ),
              )
            : b.value.includes(status)
            ? secondDimensionKeyCount
            : 0),
      0,
    );
  };

  const failed = sumWithStatus(AssetPartitionStatus.FAILED);
  const materializing = sumWithStatus(AssetPartitionStatus.MATERIALIZING);
  const materialized = sumWithStatus(AssetPartitionStatus.MATERIALIZED);

  return {
    [AssetPartitionStatus.MISSING]: total - materialized - failed - materializing,
    [AssetPartitionStatus.MATERIALIZED]: materialized,
    [AssetPartitionStatus.MATERIALIZING]: materializing,
    [AssetPartitionStatus.FAILED]: failed,
  };
}

// Given a set of ranges representing materialization status across the key space,
// find the range containing the given key and return it's state, or MISSING.
//
export function partitionStatusAtIndex(ranges: Range[], idx: number) {
  return (
    ranges.find((r) => r.start.idx <= idx && r.end.idx >= idx)?.value || [
      AssetPartitionStatus.MISSING,
    ]
  );
}

function addKeyIndexesToMaterializedRanges(
  dimensions: {name: string; partitionKeys: string[]}[],
  partitions: PartitionHealthMaterializedPartitions,
) {
  const result: Range[] = [];
  if (dimensions.length === 0) {
    return result;
  }
  if (partitions.__typename === 'DefaultPartitionStatuses') {
    const dim = dimensions[0]!;
    const spans = assembleIntoSpans(dim.partitionKeys, (key) =>
      partitions.materializedPartitions.includes(key)
        ? AssetPartitionStatus.MATERIALIZED
        : partitions.materializingPartitions.includes(key)
        ? AssetPartitionStatus.MATERIALIZING
        : partitions.failedPartitions.includes(key)
        ? AssetPartitionStatus.FAILED
        : AssetPartitionStatus.MISSING,
    );
    return spans.map(
      (s) =>
        ({
          start: {key: dim.partitionKeys[s.startIdx], idx: s.startIdx},
          end: {key: dim.partitionKeys[s.endIdx], idx: s.endIdx},
          value: [s.status as AssetPartitionStatus],
        }) as Range,
    );
  }

  for (const range of partitions.ranges) {
    if (range.__typename === 'TimePartitionRangeStatus') {
      result.push({
        start: {key: range.startKey, idx: dimensions[0]!.partitionKeys.indexOf(range.startKey)},
        end: {key: range.endKey, idx: dimensions[0]!.partitionKeys.indexOf(range.endKey)},
        value: [rangeStatusToState(range.status)],
      });
    } else if (range.__typename === 'MaterializedPartitionRangeStatuses2D') {
      if (dimensions.length !== 2) {
        warnUnlessTest('[addKeyIndexesToMaterializedRanges] Found 2D health data for 1D asset');
        return result;
      }
      const [dim0, dim1] = dimensions;
      const subranges: Range[] = addKeyIndexesToMaterializedRanges([dim1!], range.secondaryDim);
      const value = partitionStatusGivenRanges(subranges, dim1!.partitionKeys.length);
      if (isEqual(value, [AssetPartitionStatus.MISSING])) {
        continue; // should not happen, just for Typescript correctness
      }
      result.push({
        value,
        subranges,
        start: {
          key: range.primaryDimStartKey,
          idx: dim0!.partitionKeys.indexOf(range.primaryDimStartKey),
        },
        end: {
          key: range.primaryDimEndKey,
          idx: dim0!.partitionKeys.indexOf(range.primaryDimEndKey),
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
        start: {key: allKeys[0]!, idx: 0},
        end: {key: allKeys[allKeys.length - 1]!, idx: allKeys.length - 1},
        value: [AssetPartitionStatus.MATERIALIZED],
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
    if (ranges.length && idx === ranges[ranges.length - 1]!.end.idx + 1) {
      ranges[ranges.length - 1]!.end = {idx, key: allKeys[idx]!};
    } else {
      ranges.push({
        start: {idx, key: allKeys[idx]!},
        end: {idx, key: allKeys[idx]!},
        value: [AssetPartitionStatus.MATERIALIZED],
      });
    }
  }

  return ranges;
}

// Note: assetLastMaterializedAt is used as a "hint" - if the input value changes, it's
// a sign that we should invalidate and reload previously loaded health stats. We don't
// clear them immediately to avoid an empty state. You can generate a hint from the
// minimal LiveData using healthRefreshHintFromLiveData.
//
export function usePartitionHealthData(
  assetKeys: AssetKey[],
  assetsCacheKey = '',
  cacheClearStrategy: 'immediate' | 'background' = 'background',
) {
  const [partitionsLastUpdated, setPartitionsLastUpdatedAt] = useState<string>('');
  usePartitionDataSubscriber(() => {
    setPartitionsLastUpdatedAt(Date.now().toString());
  });

  const cacheKey = `${assetsCacheKey}-${partitionsLastUpdated}`;

  const [result, setResult] = useState<(PartitionHealthData & {fetchedAt: string})[]>([]);
  const client = useApolloClient();

  const assetKeyJSONs = assetKeys.map((k) => JSON.stringify(k));
  const assetKeyJSON = JSON.stringify(assetKeyJSONs);
  const missingKeyJSON = assetKeyJSONs.find(
    (k) => !result.some((r) => JSON.stringify(r.assetKey) === k && r.fetchedAt === cacheKey),
  );

  // Fetching partition health ranges can take a while -- if the "Background" refresh
  // style is enabled, fill our `result` state with whatever we can from the Apollo
  // cache. This is especially helpful if you're navigating between assets in the UI.
  useEffect(() => {
    if (cacheClearStrategy === 'immediate') {
      return;
    }
    setResult((result) => {
      const resultByKey = keyBy(result, (r) => JSON.stringify(r.assetKey));
      return JSON.parse(assetKeyJSON)
        .map((assetKeyJSON: string) => {
          const assetKey = JSON.parse(assetKeyJSON);
          const hookCached = resultByKey[assetKeyJSON];
          if (hookCached) {
            return hookCached;
          }
          const clientCached = client.cache.readQuery<
            PartitionHealthQuery,
            PartitionHealthQueryVariables
          >({
            query: PARTITION_HEALTH_QUERY,
            variables: {assetKey: {path: assetKey.path}},
          });
          if (clientCached) {
            return {...buildPartitionHealthData(clientCached, assetKey), fetchedAt: 0};
          }
          return null;
        })
        .filter(Boolean);
    });
  }, [assetKeyJSON, cacheClearStrategy, client.cache]);

  const [loading, setLoading] = useState(true);
  useBlockTraceUntilTrue('usePartitionHealthData', !loading);

  // Refresh state health ranges, one asset key at a time. This kicks off one
  // request and then missingKeyJSON updates when that is complete, kicking
  // off the next query.
  useMemo(() => {
    if (!missingKeyJSON) {
      setLoading(false);
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
        {...loaded, fetchedAt: cacheKey},
      ]);
    };
    run();
  }, [client, missingKeyJSON, cacheKey]);

  const data = useMemo(() => {
    const assetKeyJSONs = JSON.parse(assetKeyJSON);
    return result.filter(
      (r) =>
        assetKeyJSONs.includes(JSON.stringify(r.assetKey)) &&
        (r.fetchedAt === cacheKey || cacheClearStrategy === 'background'),
    );
  }, [assetKeyJSON, result, cacheKey, cacheClearStrategy]);
  useBlockTraceUntilTrue('usePartitionHealthData', data.length === assetKeys.length);
  return data;
}

// This function returns a string value that changes when the partition health bar
// or partition events page needs to be reloaded based on the partition counts or
// a new run / run failure.
//
export const healthRefreshHintFromLiveData = (liveData: LiveDataForNode | undefined) =>
  liveData
    ? `${liveData.lastMaterialization?.timestamp},${liveData.runWhichFailedToMaterialize
        ?.id},${JSON.stringify(liveData.partitionStats)}`
    : `-`;

const rangeStatusToState = (rangeStatus: PartitionRangeStatus) =>
  rangeStatus === PartitionRangeStatus.MATERIALIZED
    ? AssetPartitionStatus.MATERIALIZED
    : rangeStatus === PartitionRangeStatus.MATERIALIZING
    ? AssetPartitionStatus.MATERIALIZING
    : AssetPartitionStatus.FAILED;

export const PARTITION_HEALTH_QUERY = gql`
  query PartitionHealthQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        partitionKeysByDimension {
          name
          type
          partitionKeys
        }
        assetPartitionStatuses {
          ... on TimePartitionStatuses {
            ranges {
              status
              startTime
              endTime
              startKey
              endKey
            }
          }
          ... on DefaultPartitionStatuses {
            materializedPartitions
            materializingPartitions
            failedPartitions
          }
          ... on MultiPartitionStatuses {
            primaryDimensionName
            ranges {
              primaryDimStartKey
              primaryDimEndKey
              primaryDimStartTime
              primaryDimEndTime
              secondaryDim {
                ... on TimePartitionStatuses {
                  ranges {
                    status
                    startTime
                    endTime
                    startKey
                    endKey
                  }
                }
                ... on DefaultPartitionStatuses {
                  materializedPartitions
                  materializingPartitions
                  failedPartitions
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
