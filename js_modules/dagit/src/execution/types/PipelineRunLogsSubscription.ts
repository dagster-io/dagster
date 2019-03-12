/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL subscription operation: PipelineRunLogsSubscription
// ====================================================

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent_run {
  __typename: "PipelineRun";
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent_run;
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_run {
  __typename: "PipelineRun";
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_run;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_step;
  error: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent_error;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_run {
  __typename: "PipelineRun";
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_run;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent_step;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_StepMaterializationEvent_run {
  __typename: "PipelineRun";
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_StepMaterializationEvent_run;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_messages_StepMaterializationEvent_step;
  fileLocation: string;
  fileName: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_PipelineProcessStartedEvent_run {
  __typename: "PipelineRun";
  runId: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_messages_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  run: PipelineRunLogsSubscription_pipelineRunLogs_messages_PipelineProcessStartedEvent_run;
  message: string;
  timestamp: string;
  level: LogLevel;
  processId: number;
}

export type PipelineRunLogsSubscription_pipelineRunLogs_messages = PipelineRunLogsSubscription_pipelineRunLogs_messages_LogMessageEvent | PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepFailureEvent | PipelineRunLogsSubscription_pipelineRunLogs_messages_ExecutionStepStartEvent | PipelineRunLogsSubscription_pipelineRunLogs_messages_StepMaterializationEvent | PipelineRunLogsSubscription_pipelineRunLogs_messages_PipelineProcessStartedEvent;

export interface PipelineRunLogsSubscription_pipelineRunLogs {
  __typename: "PipelineRunLogsSubscriptionPayload";
  messages: PipelineRunLogsSubscription_pipelineRunLogs_messages[];
}

export interface PipelineRunLogsSubscription {
  pipelineRunLogs: PipelineRunLogsSubscription_pipelineRunLogs;
}

export interface PipelineRunLogsSubscriptionVariables {
  runId: string;
  after?: any | null;
}
