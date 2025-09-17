// Generated GraphQL types, do not edit manually.

import * as Types from '../../graphql/types';

export type AssetLiveRunLogsSubscriptionVariables = Types.Exact<{
  runId: Types.Scalars['ID']['input'];
}>;

export type AssetLiveRunLogsSubscription = {
  __typename: 'Subscription';
  pipelineRunLogs:
    | {__typename: 'PipelineRunLogsSubscriptionFailure'}
    | {
        __typename: 'PipelineRunLogsSubscriptionSuccess';
        messages: Array<
          | {__typename: 'AlertFailureEvent'}
          | {__typename: 'AlertStartEvent'}
          | {__typename: 'AlertSuccessEvent'}
          | {
              __typename: 'AssetCheckEvaluationEvent';
              evaluation: {
                __typename: 'AssetCheckEvaluation';
                assetKey: {__typename: 'AssetKey'; path: Array<string>};
              };
            }
          | {__typename: 'AssetCheckEvaluationPlannedEvent'}
          | {__typename: 'AssetCheckRequestedEvent'}
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
          | {
              __typename: 'FailedToMaterializeEvent';
              assetKey: {__typename: 'AssetKey'; path: Array<string>} | null;
            }
          | {__typename: 'HandledOutputEvent'}
          | {__typename: 'HealthChangedEvent'}
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

export const AssetLiveRunLogsSubscriptionVersion = 'd3ae8fb8b8500d37715da27d84b0840e19a175f27f6e62cc859473345a20f64d';
