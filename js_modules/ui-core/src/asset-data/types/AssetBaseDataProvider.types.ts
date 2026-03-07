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
    startTime: number | null;
    endTime: number | null;
  } | null;
};

export type AssetLatestInfoRunFragment = {
  __typename: 'Run';
  status: Types.RunStatus;
  startTime: number | null;
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
    stepKey: string | null;
  }>;
  assetObservations: Array<{
    __typename: 'ObservationEvent';
    timestamp: string;
    runId: string;
    stepKey: string | null;
  }>;
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
          partitionDefinition: {
            __typename: 'PartitionDefinition';
            name: string | null;
            description: string;
          } | null;
          partitionStatuses:
            | {
                __typename: 'AssetCheckDefaultPartitionStatuses';
                succeededPartitions: Array<string>;
                failedPartitions: Array<string>;
                inProgressPartitions: Array<string>;
                skippedPartitions: Array<string>;
                executionFailedPartitions: Array<string>;
              }
            | {
                __typename: 'AssetCheckMultiPartitionStatuses';
                primaryDimensionName: string;
                ranges: Array<{
                  __typename: 'AssetCheckMultiPartitionRangeStatuses';
                  primaryDimStartKey: string;
                  primaryDimEndKey: string;
                  secondaryDim:
                    | {
                        __typename: 'AssetCheckDefaultPartitionStatuses';
                        succeededPartitions: Array<string>;
                        failedPartitions: Array<string>;
                        inProgressPartitions: Array<string>;
                        skippedPartitions: Array<string>;
                        executionFailedPartitions: Array<string>;
                      }
                    | {
                        __typename: 'AssetCheckTimePartitionStatuses';
                        ranges: Array<{
                          __typename: 'AssetCheckTimePartitionRangeStatus';
                          startKey: string;
                          endKey: string;
                          status: Types.AssetCheckPartitionRangeStatus;
                        }>;
                      };
                }>;
              }
            | {
                __typename: 'AssetCheckTimePartitionStatuses';
                ranges: Array<{
                  __typename: 'AssetCheckTimePartitionRangeStatus';
                  startKey: string;
                  endKey: string;
                  status: Types.AssetCheckPartitionRangeStatus;
                }>;
              }
            | null;
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
  stepKey: string | null;
};

export type AssetNodeLiveObservationFragment = {
  __typename: 'ObservationEvent';
  timestamp: string;
  runId: string;
  stepKey: string | null;
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
  partitionDefinition: {
    __typename: 'PartitionDefinition';
    name: string | null;
    description: string;
  } | null;
  partitionStatuses:
    | {
        __typename: 'AssetCheckDefaultPartitionStatuses';
        succeededPartitions: Array<string>;
        failedPartitions: Array<string>;
        inProgressPartitions: Array<string>;
        skippedPartitions: Array<string>;
        executionFailedPartitions: Array<string>;
      }
    | {
        __typename: 'AssetCheckMultiPartitionStatuses';
        primaryDimensionName: string;
        ranges: Array<{
          __typename: 'AssetCheckMultiPartitionRangeStatuses';
          primaryDimStartKey: string;
          primaryDimEndKey: string;
          secondaryDim:
            | {
                __typename: 'AssetCheckDefaultPartitionStatuses';
                succeededPartitions: Array<string>;
                failedPartitions: Array<string>;
                inProgressPartitions: Array<string>;
                skippedPartitions: Array<string>;
                executionFailedPartitions: Array<string>;
              }
            | {
                __typename: 'AssetCheckTimePartitionStatuses';
                ranges: Array<{
                  __typename: 'AssetCheckTimePartitionRangeStatus';
                  startKey: string;
                  endKey: string;
                  status: Types.AssetCheckPartitionRangeStatus;
                }>;
              };
        }>;
      }
    | {
        __typename: 'AssetCheckTimePartitionStatuses';
        ranges: Array<{
          __typename: 'AssetCheckTimePartitionRangeStatus';
          startKey: string;
          endKey: string;
          status: Types.AssetCheckPartitionRangeStatus;
        }>;
      }
    | null;
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
      stepKey: string | null;
    }>;
    assetObservations: Array<{
      __typename: 'ObservationEvent';
      timestamp: string;
      runId: string;
      stepKey: string | null;
    }>;
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
            partitionDefinition: {
              __typename: 'PartitionDefinition';
              name: string | null;
              description: string;
            } | null;
            partitionStatuses:
              | {
                  __typename: 'AssetCheckDefaultPartitionStatuses';
                  succeededPartitions: Array<string>;
                  failedPartitions: Array<string>;
                  inProgressPartitions: Array<string>;
                  skippedPartitions: Array<string>;
                  executionFailedPartitions: Array<string>;
                }
              | {
                  __typename: 'AssetCheckMultiPartitionStatuses';
                  primaryDimensionName: string;
                  ranges: Array<{
                    __typename: 'AssetCheckMultiPartitionRangeStatuses';
                    primaryDimStartKey: string;
                    primaryDimEndKey: string;
                    secondaryDim:
                      | {
                          __typename: 'AssetCheckDefaultPartitionStatuses';
                          succeededPartitions: Array<string>;
                          failedPartitions: Array<string>;
                          inProgressPartitions: Array<string>;
                          skippedPartitions: Array<string>;
                          executionFailedPartitions: Array<string>;
                        }
                      | {
                          __typename: 'AssetCheckTimePartitionStatuses';
                          ranges: Array<{
                            __typename: 'AssetCheckTimePartitionRangeStatus';
                            startKey: string;
                            endKey: string;
                            status: Types.AssetCheckPartitionRangeStatus;
                          }>;
                        };
                  }>;
                }
              | {
                  __typename: 'AssetCheckTimePartitionStatuses';
                  ranges: Array<{
                    __typename: 'AssetCheckTimePartitionRangeStatus';
                    startKey: string;
                    endKey: string;
                    status: Types.AssetCheckPartitionRangeStatus;
                  }>;
                }
              | null;
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
      startTime: number | null;
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

export type AssetNodeLiveFreshnessInfoFragment = {
  __typename: 'AssetFreshnessInfo';
  currentMinutesLate: number | null;
};

export const AssetGraphLiveQueryVersion = 'c8f79137c3b2f47eb62184e17c8cd11a9c6f1216561a7fe956ec638af9b2dfbd';

export const AssetsFreshnessInfoQueryVersion = '1049ac5edde1a0f5c16dd8342020c30db8603477f6d7760712c5784a71bdbc01';
