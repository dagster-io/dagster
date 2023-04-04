// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetLatestInfoFragment = {
  __typename: 'AssetLatestInfo';
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

export type AssetGraphLiveQueryVariables = Types.Exact<{
  assetKeys: Array<Types.AssetKeyInput> | Types.AssetKeyInput;
}>;

export type AssetGraphLiveQuery = {
  __typename: 'DagitQuery';
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
    freshnessPolicy: {
      __typename: 'FreshnessPolicy';
      maximumLagMinutes: number;
      cronSchedule: string | null;
      cronScheduleTimezone: string | null;
    } | null;
    freshnessInfo: {__typename: 'AssetFreshnessInfo'; currentMinutesLate: number | null} | null;
    assetObservations: Array<{__typename: 'ObservationEvent'; timestamp: string; runId: string}>;
    staleCauses: Array<{
      __typename: 'StaleCause';
      reason: string;
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

export type AssetLiveRunLogsSubscriptionVariables = Types.Exact<{
  runId: Types.Scalars['ID'];
}>;

export type AssetLiveRunLogsSubscription = {
  __typename: 'DagitSubscription';
  pipelineRunLogs:
    | {__typename: 'PipelineRunLogsSubscriptionFailure'}
    | {
        __typename: 'PipelineRunLogsSubscriptionSuccess';
        messages: Array<
          | {__typename: 'AlertFailureEvent'}
          | {__typename: 'AlertStartEvent'}
          | {__typename: 'AlertSuccessEvent'}
          | {
              __typename: 'AssetMaterializationPlannedEvent';
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {__typename: 'EngineEvent'}
          | {__typename: 'ExecutionStepFailureEvent'; stepKey: string | null}
          | {__typename: 'ExecutionStepInputEvent'}
          | {__typename: 'ExecutionStepOutputEvent'}
          | {__typename: 'ExecutionStepRestartEvent'}
          | {__typename: 'ExecutionStepSkippedEvent'}
          | {__typename: 'ExecutionStepStartEvent'; stepKey: string | null}
          | {__typename: 'ExecutionStepSuccessEvent'}
          | {__typename: 'ExecutionStepUpForRetryEvent'}
          | {__typename: 'HandledOutputEvent'}
          | {__typename: 'HookCompletedEvent'}
          | {__typename: 'HookErroredEvent'}
          | {__typename: 'HookSkippedEvent'}
          | {__typename: 'LoadedInputEvent'}
          | {__typename: 'LogMessageEvent'}
          | {__typename: 'LogsCapturedEvent'}
          | {
              __typename: 'MaterializationEvent';
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {__typename: 'ObjectStoreOperationEvent'}
          | {
              __typename: 'ObservationEvent';
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {__typename: 'ResourceInitFailureEvent'}
          | {__typename: 'ResourceInitStartedEvent'}
          | {__typename: 'ResourceInitSuccessEvent'}
          | {__typename: 'RunCanceledEvent'}
          | {__typename: 'RunCancelingEvent'}
          | {__typename: 'RunDequeuedEvent'}
          | {__typename: 'RunEnqueuedEvent'}
          | {__typename: 'RunFailureEvent'}
          | {__typename: 'RunStartEvent'}
          | {__typename: 'RunStartingEvent'}
          | {__typename: 'RunSuccessEvent'}
          | {__typename: 'StepExpectationResultEvent'}
          | {__typename: 'StepWorkerStartedEvent'}
          | {__typename: 'StepWorkerStartingEvent'}
        >;
      };
};
