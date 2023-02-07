// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetNodeLiveFragment = {
  __typename: 'AssetNode';
  id: string;
  opNames: Array<string>;
  currentLogicalVersion: string | null;
  projectedLogicalVersion: string | null;
  repository: {__typename: 'Repository'; id: string};
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  assetMaterializations: Array<{
    __typename: 'MaterializationEvent';
    timestamp: string;
    runId: string;
  }>;
  freshnessPolicy: {
    __typename: 'FreshnessPolicy';
    maximumLagMinutes: number;
    cronSchedule: string | null;
  } | null;
  freshnessInfo: {__typename: 'AssetFreshnessInfo'; currentMinutesLate: number | null} | null;
  assetObservations: Array<{__typename: 'ObservationEvent'; timestamp: string; runId: string}>;
  partitionStats: {
    __typename: 'PartitionStats';
    numMaterialized: number;
    numPartitions: number;
  } | null;
};

export type AssetNodeLiveFreshnessPolicyFragment = {
  __typename: 'FreshnessPolicy';
  maximumLagMinutes: number;
  cronSchedule: string | null;
};

export type AssetNodeLiveFreshnessInfoFragment = {
  __typename: 'AssetFreshnessInfo';
  currentMinutesLate: number | null;
};

export type AssetNodeLiveMaterializationFragment = {
  __typename: 'MaterializationEvent';
  timestamp: string;
  runId: string;
};

export type AssetNodeLiveObservationFragment = {
  __typename: 'ObservationEvent';
  timestamp: string;
  runId: string;
};

export type AssetNodeFragment = {
  __typename: 'AssetNode';
  id: string;
  graphName: string | null;
  jobNames: Array<string>;
  opNames: Array<string>;
  opVersion: string | null;
  description: string | null;
  computeKind: string | null;
  isPartitioned: boolean;
  isObservable: boolean;
  isSource: boolean;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
};

export type AssetNodeKeyFragment = {__typename: 'AssetKey'; path: Array<string>};
