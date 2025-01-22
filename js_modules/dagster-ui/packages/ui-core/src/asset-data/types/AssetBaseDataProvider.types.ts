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
  repository: {__typename: 'Repository'; id: string};
  assetKey: {__typename: 'AssetKey'; path: Array<string>};
  assetMaterializations: Array<{
    __typename: 'MaterializationEvent';
    timestamp: string;
    runId: string;
  }>;
  assetObservations: Array<{__typename: 'ObservationEvent'; timestamp: string; runId: string}>;
  assetChecksOrError:
    | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
    | {__typename: 'AssetCheckNeedsMigrationError'}
    | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
    | {
        __typename: 'AssetChecks';
        checks: Array<{
          __typename: 'AssetCheck';
          name: string;
          canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
          executionForLatestMaterialization: {
            __typename: 'AssetCheckExecution';
            id: string;
            runId: string;
            status: Types.AssetCheckExecutionResolvedStatus;
            timestamp: number;
            stepKey: string | null;
            evaluation: {
              __typename: 'AssetCheckEvaluation';
              severity: Types.AssetCheckSeverity;
            } | null;
          } | null;
        }>;
      };
  partitionStats: {
    __typename: 'PartitionStats';
    numMaterialized: number;
    numMaterializing: number;
    numPartitions: number;
    numFailed: number;
  } | null;
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

export type AssetCheckLiveFragment = {
  __typename: 'AssetCheck';
  name: string;
  canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
  executionForLatestMaterialization: {
    __typename: 'AssetCheckExecution';
    id: string;
    runId: string;
    status: Types.AssetCheckExecutionResolvedStatus;
    timestamp: number;
    stepKey: string | null;
    evaluation: {__typename: 'AssetCheckEvaluation'; severity: Types.AssetCheckSeverity} | null;
  } | null;
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
    repository: {__typename: 'Repository'; id: string};
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    assetMaterializations: Array<{
      __typename: 'MaterializationEvent';
      timestamp: string;
      runId: string;
    }>;
    assetObservations: Array<{__typename: 'ObservationEvent'; timestamp: string; runId: string}>;
    assetChecksOrError:
      | {__typename: 'AssetCheckNeedsAgentUpgradeError'}
      | {__typename: 'AssetCheckNeedsMigrationError'}
      | {__typename: 'AssetCheckNeedsUserCodeUpgrade'}
      | {
          __typename: 'AssetChecks';
          checks: Array<{
            __typename: 'AssetCheck';
            name: string;
            canExecuteIndividually: Types.AssetCheckCanExecuteIndividually;
            executionForLatestMaterialization: {
              __typename: 'AssetCheckExecution';
              id: string;
              runId: string;
              status: Types.AssetCheckExecutionResolvedStatus;
              timestamp: number;
              stepKey: string | null;
              evaluation: {
                __typename: 'AssetCheckEvaluation';
                severity: Types.AssetCheckSeverity;
              } | null;
            } | null;
          }>;
        };
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

export type AssetsFreshnessInfoQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetsFreshnessInfoQuery = {
  __typename: 'Query';
  assetNodes: Array<{
    __typename: 'AssetNode';
    id: string;
    assetKey: {__typename: 'AssetKey'; path: Array<string>};
    freshnessInfo: {__typename: 'AssetFreshnessInfo'; currentMinutesLate: number | null} | null;
  }>;
};

export type AssetFreshnessInfoFragment = {
  __typename: 'AssetFreshnessInfo';
  currentMinutesLate: number | null;
};

export const AssetGraphLiveQueryVersion = 'd65025ff4ff394938e261d28393a15fa2c5095afb19bdbf6171bdda29e762497';

export const AssetsFreshnessInfoQueryVersion = '5ced7579607f729f8423937a9baba83b0e5080574d8d3a7611e1f7dc6c931d60';
