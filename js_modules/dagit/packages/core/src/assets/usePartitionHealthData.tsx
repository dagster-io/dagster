import {gql, useApolloClient} from '@apollo/client';
import isEqual from 'lodash/isEqual';
import React from 'react';

import {assertUnreachable} from '../app/Util';
import {PartitionState} from '../partitions/PartitionStatus';

import {mergedStates} from './MultipartitioningSupport';
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
  stateForSingleDimension: (
    dimensionIdx: number,
    dimensionKey: string,
    otherDimensionSelectedKeys?: string[],
  ) => PartitionState;
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
      console.warn('[stateForKey] called with incorrect number of dimensions');
      return PartitionState.MISSING;
    }

    const dIndexes = dimensionKeys.map((key, idx) => dimensions[idx].partitionKeys.indexOf(key));
    const d0Range = ranges.find((r) => r.start.idx <= dIndexes[0] && r.end.idx >= dIndexes[0]);

    if (!d0Range) {
      return PartitionState.MISSING;
    }
    if (!d0Range.subranges) {
      return PartitionState.SUCCESS; // 1D case
    }
    const d1Range = d0Range.subranges.find(
      (r) => r.start.idx <= dIndexes[1] && r.end.idx >= dIndexes[1],
    );
    return d1Range ? PartitionState.SUCCESS : PartitionState.MISSING;
  };

  const stateForSingleDimension = (
    dimensionIdx: number,
    dimensionKey: string,
    otherDimensionSelectedKeys?: string[], // using this feature is slow
  ) => {
    if (dimensions.length === 0) {
      return PartitionState.MISSING;
    }
    if (dimensionIdx === 0 && dimensions.length === 1) {
      return stateForKeyWithRangeOrdering([dimensionKey]);
    }

    const [d0, d1] = dimensions;
    if (isRangeDataInverted) {
      dimensionIdx = 1 - dimensionIdx;
    }

    if (dimensionIdx === 0) {
      if (otherDimensionSelectedKeys) {
        return mergedStates(
          otherDimensionSelectedKeys.map((k) => stateForKeyWithRangeOrdering([dimensionKey, k])),
        );
      }
      const d0Idx = d0.partitionKeys.indexOf(dimensionKey);
      const d0Range = ranges.find((r) => r.start.idx <= d0Idx && r.end.idx >= d0Idx);
      return d0Range?.value || PartitionState.MISSING;
    }
    if (dimensionIdx === 1) {
      if (otherDimensionSelectedKeys) {
        return mergedStates(
          otherDimensionSelectedKeys.map((k) => stateForKeyWithRangeOrdering([k, dimensionKey])),
        );
      }

      const d1Idx = d1.partitionKeys.indexOf(dimensionKey);
      const d0RangesContainingSubrangeWithD1Idx = ranges.filter((r) =>
        r.subranges?.some((sr) => sr.start.idx <= d1Idx && sr.end.idx >= d1Idx),
      );
      if (d0RangesContainingSubrangeWithD1Idx.length === 0) {
        return PartitionState.MISSING;
      }
      if (d0RangesContainingSubrangeWithD1Idx.length < ranges.length) {
        return PartitionState.SUCCESS_MISSING;
      }
      return rangesCoverAll(d0RangesContainingSubrangeWithD1Idx, d0.partitionKeys.length)
        ? PartitionState.SUCCESS
        : PartitionState.SUCCESS_MISSING;
    }

    throw new Error('stateForSingleDimension asked for third dimension');
  };

  const result: PartitionHealthData = {
    assetKey: loadKey,
    dimensions: __dims.map((d) => ({name: d.name, partitionKeys: d.partitionKeys})),
    stateForKey,
    stateForSingleDimension,
  };

  return result;
}

// Add indexes to the materializedPartitions data so that we can find specific keys in
// the range structures without having to indexOf the start and end key of every range.
//
type Range = {
  start: {key: string; idx: number};
  end: {key: string; idx: number};
  value: PartitionState.SUCCESS | PartitionState.SUCCESS_MISSING;
  subranges?: Range[];
};

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
    const count = dim.partitionKeys.length;
    if (materializedPartitions.materializedPartitions.length === count) {
      return [
        {
          start: {key: dim.partitionKeys[0], idx: 0},
          end: {key: dim.partitionKeys[count - 1], idx: count - 1},
          value: PartitionState.SUCCESS as const,
        },
      ];
    } else {
      return materializedPartitions.materializedPartitions.map<Range>((key) => {
        const idx = dim.partitionKeys.indexOf(key);
        return {start: {key, idx}, end: {key, idx}, value: PartitionState.SUCCESS};
      });
    }
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
        console.warn('[addKeyIndexesToMaterializedRanges] Found 2D health data for 1D asset');
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
