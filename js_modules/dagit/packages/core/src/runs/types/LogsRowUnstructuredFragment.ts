// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsRowUnstructuredFragment
// ====================================================

export interface LogsRowUnstructuredFragment {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineEnqueuedEvent" | "PipelineDequeuedEvent" | "PipelineStartingEvent" | "PipelineCancelingEvent" | "PipelineCanceledEvent" | "PipelineSuccessEvent" | "HandledOutputEvent" | "LoadedInputEvent" | "LogsCapturedEvent" | "ObjectStoreOperationEvent" | "StepExpectationResultEvent" | "StepMaterializationEvent" | "EngineEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "HookErroredEvent" | "AlertStartEvent" | "AlertSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
}
