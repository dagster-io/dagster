// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsRowUnstructuredFragment
// ====================================================

export interface LogsRowUnstructuredFragment_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsRowUnstructuredFragment {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineInitFailureEvent" | "PipelineProcessExitedEvent" | "PipelineProcessStartedEvent" | "PipelineProcessStartEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "ObjectStoreOperationEvent" | "StepExpectationResultEvent" | "StepMaterializationEvent" | "EngineEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsRowUnstructuredFragment_step | null;
}
