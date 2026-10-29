/** Internal type. DO NOT USE DIRECTLY. */
type Exact<T extends {[key: string]: unknown}> = {[K in keyof T]: T[K]};
/** Internal type. DO NOT USE DIRECTLY. */
export type Incremental<T> =
  | T
  | {[P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never};
// Generated GraphQL types, do not edit manually.

import * as Types from '../../../graphql/types';

export type DagsterEventType =
  | 'ALERT_FAILURE'
  | 'ALERT_START'
  | 'ALERT_SUCCESS'
  | 'ASSET_CHECK_EVALUATION'
  | 'ASSET_CHECK_EVALUATION_PLANNED'
  | 'ASSET_FAILED_TO_MATERIALIZE'
  | 'ASSET_HEALTH_CHANGED'
  | 'ASSET_MATERIALIZATION'
  | 'ASSET_MATERIALIZATION_PLANNED'
  | 'ASSET_OBSERVATION'
  | 'ASSET_STORE_OPERATION'
  | 'ASSET_WIPED'
  | 'CODE_LOCATION_UPDATED'
  | 'ENGINE_EVENT'
  | 'FRESHNESS_STATE_CHANGE'
  | 'FRESHNESS_STATE_EVALUATION'
  | 'HANDLED_OUTPUT'
  | 'HOOK_COMPLETED'
  | 'HOOK_ERRORED'
  | 'HOOK_SKIPPED'
  | 'LOADED_INPUT'
  | 'LOGS_CAPTURED'
  | 'OBJECT_STORE_OPERATION'
  | 'PIPELINE_CANCELED'
  | 'PIPELINE_CANCELING'
  | 'PIPELINE_DEQUEUED'
  | 'PIPELINE_ENQUEUED'
  | 'PIPELINE_FAILURE'
  | 'PIPELINE_START'
  | 'PIPELINE_STARTING'
  | 'PIPELINE_SUCCESS'
  | 'RESOURCE_INIT_FAILURE'
  | 'RESOURCE_INIT_STARTED'
  | 'RESOURCE_INIT_SUCCESS'
  | 'RUN_CANCELED'
  | 'RUN_CANCELING'
  | 'RUN_DEQUEUED'
  | 'RUN_ENQUEUED'
  | 'RUN_FAILURE'
  | 'RUN_START'
  | 'RUN_STARTING'
  | 'RUN_SUCCESS'
  | 'STEP_EXPECTATION_RESULT'
  | 'STEP_FAILURE'
  | 'STEP_INPUT'
  | 'STEP_OUTPUT'
  | 'STEP_RESTARTED'
  | 'STEP_SKIPPED'
  | 'STEP_START'
  | 'STEP_SUCCESS'
  | 'STEP_UP_FOR_RETRY'
  | 'STEP_WORKER_STARTED'
  | 'STEP_WORKER_STARTING';

export type LogLevel = 'CRITICAL' | 'DEBUG' | 'ERROR' | 'INFO' | 'WARNING';

export type RunStatus =
  | 'CANCELED'
  | 'CANCELING'
  | 'FAILURE'
  | 'MANAGED'
  | 'NOT_STARTED'
  | 'QUEUED'
  | 'STARTED'
  | 'STARTING'
  | 'SUCCESS';

export type StepEventStatus = 'FAILURE' | 'IN_PROGRESS' | 'SKIPPED' | 'SUCCESS';

export type MobileRunQueryVariables = Exact<{
  runId: string;
  logLimit: number;
}>;

export type MobileRunQuery = {
  __typename: 'Query';
  runOrError:
    | {__typename: 'PythonError'}
    | {
        __typename: 'Run';
        id: string;
        runId: string;
        status: Types.RunStatus;
        pipelineName: string;
        startTime: number | null;
        endTime: number | null;
        canTerminate: boolean;
        stepStats: Array<{
          __typename: 'RunStepStats';
          stepKey: string;
          status: Types.StepEventStatus | null;
          startTime: number | null;
          endTime: number | null;
          attempts: Array<{__typename: 'RunMarker'; startTime: number | null}>;
        }>;
      }
    | {__typename: 'RunNotFoundError'};
  logsForRun:
    | {
        __typename: 'EventConnection';
        hasMore: boolean;
        events: Array<
          | {
              __typename: 'AlertFailureEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertStartEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AlertSuccessEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetCheckEvaluationEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetCheckEvaluationPlannedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'AssetMaterializationPlannedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'EngineEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepFailureEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepInputEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepOutputEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepRestartEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSkippedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepStartEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepSuccessEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ExecutionStepUpForRetryEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'FailedToMaterializeEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HandledOutputEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HealthChangedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HookCompletedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HookErroredEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'HookSkippedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LoadedInputEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LogMessageEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'LogsCapturedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'MaterializationEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ObjectStoreOperationEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ObservationEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ResourceInitFailureEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ResourceInitStartedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'ResourceInitSuccessEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunCanceledEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunCancelingEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunDequeuedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunEnqueuedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunFailureEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunStartEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunStartingEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'RunSuccessEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'StepExpectationResultEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'StepWorkerStartedEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
          | {
              __typename: 'StepWorkerStartingEvent';
              message: string;
              timestamp: string;
              level: Types.LogLevel;
              stepKey: string | null;
              eventType: Types.DagsterEventType | null;
            }
        >;
      }
    | {__typename: 'PythonError'}
    | {__typename: 'RunNotFoundError'};
};
