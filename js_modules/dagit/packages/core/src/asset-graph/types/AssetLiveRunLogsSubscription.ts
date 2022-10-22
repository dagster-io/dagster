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

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "ResourceInitFailureEvent" | "ResourceInitStartedEvent" | "ResourceInitSuccessEvent" | "RunFailureEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "StepWorkerStartedEvent" | "StepWorkerStartingEvent" | "HandledOutputEvent" | "LoadedInputEvent" | "LogsCapturedEvent" | "ObjectStoreOperationEvent" | "StepExpectationResultEvent" | "EngineEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "HookErroredEvent" | "AlertStartEvent" | "AlertSuccessEvent" | "AlertFailureEvent";
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_AssetMaterializationPlannedEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_AssetMaterializationPlannedEvent {
  __typename: "AssetMaterializationPlannedEvent";
  assetKey: AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_AssetMaterializationPlannedEvent_assetKey | null;
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_MaterializationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_MaterializationEvent {
  __typename: "MaterializationEvent";
  assetKey: AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_MaterializationEvent_assetKey | null;
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ObservationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ObservationEvent {
  __typename: "ObservationEvent";
  assetKey: AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ObservationEvent_assetKey | null;
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent";
  stepKey: string | null;
}

export interface AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  stepKey: string | null;
}

export type AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages = AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepInputEvent | AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_AssetMaterializationPlannedEvent | AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_MaterializationEvent | AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ObservationEvent | AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepStartEvent | AssetLiveRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent;

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
