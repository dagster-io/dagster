// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetNodeLiveFragment = {
  __typename: 'AssetNode';
  id: string;
  opNames: Array<string>;
  staleStatus: Types.StaleStatus | null;
  repository: {__typename: 'Repository'; id: string};
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  assetMaterializations: Array<{
    __typename: 'MaterializationEvent';
    timestamp: string;
    runId: string;
  }>;
  assetObservations: Array<{__typename: 'ObservationEvent'; timestamp: string; runId: string}>;
  freshnessInfo: {__typename: 'AssetFreshnessInfo'; currentMinutesLate: number | null} | null;
  staleCauses: Array<{
    __typename: 'StaleCause';
    reason: string;
    category: Types.StaleCauseCategory;
    key: {__typename: 'AssetKey'; path: Array<string>};
    dependency: {__typename: 'AssetKey'; path: Array<string>} | null;
  }>;
  partitionStats: {
    __typename: 'PartitionStats';
    numMaterialized: number;
    numMaterializing: number;
    numPartitions: number;
    numFailed: number;
  } | null;
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
  hasMaterializePermission: boolean;
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
