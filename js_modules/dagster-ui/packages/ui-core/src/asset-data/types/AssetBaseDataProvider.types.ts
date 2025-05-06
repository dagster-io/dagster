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
        }>;
      };
  lastAutoMaterializationEvaluationRecord: {
    __typename: 'AutoMaterializeAssetEvaluationRecord';
    id: string;
    evaluationId: string;
  } | null;
  partitionStats: {
    __typename: 'PartitionStats';
    numMaterialized: number;
    numMaterializing: number;
    numPartitions: number;
    numFailed: number;
  } | null;
  targetingInstigators: Array<
    | {
        __typename: 'Schedule';
        id: string;
        name: string;
        cronSchedule: string;
        executionTimezone: string | null;
        scheduleState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
        };
      }
    | {
        __typename: 'Sensor';
        id: string;
        name: string;
        sensorType: Types.SensorType;
        sensorState: {
          __typename: 'InstigationState';
          id: string;
          selectorId: string;
          status: Types.InstigationStatus;
          typeSpecificData:
            | {__typename: 'ScheduleData'}
            | {__typename: 'SensorData'; lastCursor: string | null}
            | null;
        };
      }
  >;
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
};

export type AssetNodeLiveAutoMaterializationEvaluationFragment = {
  __typename: 'AutoMaterializeAssetEvaluationRecord';
  id: string;
  evaluationId: string;
};

export type AssetNodeLiveInstigatorFragment_Schedule = {
  __typename: 'Schedule';
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  scheduleState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    status: Types.InstigationStatus;
  };
};

export type AssetNodeLiveInstigatorFragment_Sensor = {
  __typename: 'Sensor';
  id: string;
  name: string;
  sensorType: Types.SensorType;
  sensorState: {
    __typename: 'InstigationState';
    id: string;
    selectorId: string;
    status: Types.InstigationStatus;
    typeSpecificData:
      | {__typename: 'ScheduleData'}
      | {__typename: 'SensorData'; lastCursor: string | null}
      | null;
  };
};

export type AssetNodeLiveInstigatorFragment =
  | AssetNodeLiveInstigatorFragment_Schedule
  | AssetNodeLiveInstigatorFragment_Sensor;

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
          }>;
        };
    lastAutoMaterializationEvaluationRecord: {
      __typename: 'AutoMaterializeAssetEvaluationRecord';
      id: string;
      evaluationId: string;
    } | null;
    partitionStats: {
      __typename: 'PartitionStats';
      numMaterialized: number;
      numMaterializing: number;
      numPartitions: number;
      numFailed: number;
    } | null;
    targetingInstigators: Array<
      | {
          __typename: 'Schedule';
          id: string;
          name: string;
          cronSchedule: string;
          executionTimezone: string | null;
          scheduleState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
          };
        }
      | {
          __typename: 'Sensor';
          id: string;
          name: string;
          sensorType: Types.SensorType;
          sensorState: {
            __typename: 'InstigationState';
            id: string;
            selectorId: string;
            status: Types.InstigationStatus;
            typeSpecificData:
              | {__typename: 'ScheduleData'}
              | {__typename: 'SensorData'; lastCursor: string | null}
              | null;
          };
        }
    >;
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

export const AssetGraphLiveQueryVersion = '5c4700b71978e8f7e50c24e53496b184203765e77a44eccbc6fdb6f579a70fd9';

export const AssetsFreshnessInfoQueryVersion = '1049ac5edde1a0f5c16dd8342020c30db8603477f6d7760712c5784a71bdbc01';
