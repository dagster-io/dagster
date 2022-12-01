import {ApolloClient, gql, useApolloClient} from '@apollo/client';
import isEqual from 'lodash/isEqual';
import React from 'react';

import {PartitionState} from '../partitions/PartitionStatus';

import {mergedStates} from './MultipartitioningSupport';
import {AssetKey} from './types';
import {PartitionHealthQuery, PartitionHealthQueryVariables} from './types/PartitionHealthQuery';

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
  stateForPartialKey: (dimensionKeys: string[]) => PartitionState;
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

export type PartitionHealthDimensionRange = {
  dimension: PartitionHealthDimension;
  selected: string[];
};

async function loadPartitionHealthData(client: ApolloClient<any>, loadKey: AssetKey) {
  const {data} = await client.query<PartitionHealthQuery, PartitionHealthQueryVariables>({
    query: PARTITION_HEALTH_QUERY,
    fetchPolicy: 'network-only',
    variables: {
      assetKey: {path: loadKey.path},
    },
  });

  const dimensions =
    data.assetNodeOrError.__typename === 'AssetNode'
      ? data.assetNodeOrError.partitionKeysByDimension
      : [];

  const materializationStatus = (data.assetNodeOrError.__typename === 'AssetNode' &&
    data.assetNodeOrError.partitionMaterializationStatus) || {
    __typename: 'MaterializationStatusSingleDimension',
    materializationStatus: [],
  };

  const stateByKey = Object.fromEntries(
    materializationStatus.__typename === 'MaterializationStatusSingleDimension'
      ? materializationStatus.materializationStatus.map((materialized, idx) => [
          dimensions[0].partitionKeys[idx],
          materialized ? PartitionState.SUCCESS : PartitionState.MISSING,
        ])
      : materializationStatus.materializationStatusGrouped.map((dim0, idx0) => [
          dimensions[0].partitionKeys[idx0],
          Object.fromEntries(
            dim0.map((materialized, idx1) => [
              dimensions[1].partitionKeys[idx1],
              materialized ? PartitionState.SUCCESS : PartitionState.MISSING,
            ]),
          ),
        ]),
  );

  const stateForKey = (dimensionKeys: string[]): PartitionState =>
    dimensionKeys.reduce((counts, dimensionKey) => counts[dimensionKey], stateByKey);

  const stateForSingleDimension = (
    dimensionIdx: number,
    dimensionKey: string,
    otherDimensionSelectedKeys?: string[],
  ) => {
    if (dimensionIdx === 0 && dimensions.length === 1) {
      return stateForKey([dimensionKey]);
    }
    if (dimensionIdx === 0) {
      return mergedStates(
        Object.entries<PartitionState>(stateByKey[dimensionKey])
          .filter(
            ([key]) => !otherDimensionSelectedKeys || otherDimensionSelectedKeys.includes(key),
          )
          .map(([_, val]) => val),
      );
    } else if (dimensionIdx === 1) {
      return mergedStates(
        Object.entries<{[subdimensionKey: string]: PartitionState}>(stateByKey)
          .filter(
            ([key]) => !otherDimensionSelectedKeys || otherDimensionSelectedKeys.includes(key),
          )
          .map(([_, val]) => val[dimensionKey]),
      );
    } else {
      throw new Error('stateForSingleDimension asked for third dimension');
    }
  };

  const stateForPartialKey = (dimensionKeys: string[]) => {
    return dimensionKeys.length === dimensions.length
      ? stateForKey(dimensionKeys)
      : mergedStates(Object.values(stateByKey[dimensionKeys[0]]));
  };

  const result: PartitionHealthData = {
    assetKey: loadKey,
    stateForKey,
    stateForPartialKey,
    stateForSingleDimension,
    dimensions: dimensions.map((d) => ({
      name: d.name,
      partitionKeys: d.partitionKeys,
    })),
  };

  return result;
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
      const loaded = await loadPartitionHealthData(client, loadKey);
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

const PARTITION_HEALTH_QUERY = gql`
  query PartitionHealthQuery($assetKey: AssetKeyInput!) {
    assetNodeOrError(assetKey: $assetKey) {
      ... on AssetNode {
        id
        partitionKeysByDimension {
          name
          partitionKeys
        }
        partitionMaterializationStatus {
          ... on MaterializationStatusGroupedByDimension {
            materializationStatusGrouped
          }
          ... on MaterializationStatusSingleDimension {
            materializationStatus
          }
        }
      }
    }
  }
`;
