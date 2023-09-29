// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetLatestInfoFragment = {
  __typename: 'AssetLatestInfo';
  id: string;
  unstartedRunIds: Array<string>;
  inProgressRunIds: Array<string>;
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  latestRun: {
    __typename: 'Run';
    id: string;
    status: Types.RunStatus;
    endTime: number | null;
  } | null;
};

export type AssetLatestInfoRunFragment = {
  __typename: 'Run';
  status: Types.RunStatus;
  endTime: number | null;
  id: string;
};

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
  assetChecks: Array<{
    __typename: 'AssetCheck';
    name: string;
    canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
    executionForLatestMaterialization: {
      __typename: 'AssetCheckExecution';
      id: string;
      runId: string;
      status: Types.AssetCheckExecutionResolvedStatus;
      evaluation: {__typename: 'AssetCheckEvaluation'; severity: Types.AssetCheckSeverity} | null;
    } | null;
  }>;
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

export type AssetGraphLiveQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetGraphLiveQuery = {
  __typename: 'Query';
  assetNodes: Array<{
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
    assetChecks: Array<{
      __typename: 'AssetCheck';
      name: string;
      canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
      executionForLatestMaterialization: {
        __typename: 'AssetCheckExecution';
        id: string;
        runId: string;
        status: Types.AssetCheckExecutionResolvedStatus;
        evaluation: {__typename: 'AssetCheckEvaluation'; severity: Types.AssetCheckSeverity} | null;
      } | null;
    }>;
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
  }>;
  assetsLatestInfo: Array<{
    __typename: 'AssetLatestInfo';
    id: string;
    unstartedRunIds: Array<string>;
    inProgressRunIds: Array<string>;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    latestRun: {
      __typename: 'Run';
      id: string;
      status: Types.RunStatus;
      endTime: number | null;
    } | null;
  }>;
};
