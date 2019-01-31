/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunLogsUpdateFragment
// ====================================================

export interface PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  processId: number;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent_step;
  fileLocation: string | null;
  fileName: string | null;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineRunLogsUpdateFragment_logs_nodes = PipelineRunLogsUpdateFragment_logs_nodes_LogMessageEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunLogsUpdateFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunLogsUpdateFragment_logs_nodes_StepMaterializationEvent | PipelineRunLogsUpdateFragment_logs_nodes_ExecutionStepStartEvent;

export interface PipelineRunLogsUpdateFragment_logs {
  __typename: "LogMessageConnection";
  nodes: PipelineRunLogsUpdateFragment_logs_nodes[];
}

export interface PipelineRunLogsUpdateFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineRunLogsUpdateFragment_logs;
}
