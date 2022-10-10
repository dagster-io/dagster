/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: AssetLiveRunLogsSubscription
// ====================================================

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionFailure {
  __typename: "PipelineRunLogsSubscriptionFailure";
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "ResourceInitFailureEvent" | "ResourceInitStartedEvent" | "ResourceInitSuccessEvent" | "RunFailureEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "StepWorkerStartedEvent" | "StepWorkerStartingEvent" | "HandledOutputEvent" | "LoadedInputEvent" | "LogsCapturedEvent" | "ObjectStoreOperationEvent" | "StepExpectationResultEvent" | "MaterializationEvent" | "ObservationEvent" | "EngineEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "HookErroredEvent" | "AlertStartEvent" | "AlertSuccessEvent" | "AlertFailureEvent" | "AssetMaterializationPlannedEvent";
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess {
  __typename: "PipelineRunLogsSubscriptionSuccess";
  messages: AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages[];
}

export type AssetLiveRunLogsSubscription_pipelineRunLogs = AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionFailure | AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess;

export interface AssetLiveRunLogsSubscription {
  pipelineRunLogs: AssetLiveRunLogsSubscription_pipelineRunLogs;
}

export interface AssetLiveRunLogsSubscriptionVariables {
  runId: string;
}
