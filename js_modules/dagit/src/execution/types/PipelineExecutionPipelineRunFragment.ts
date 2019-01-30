/* tslint:disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineExecutionPipelineRunFragment
// ====================================================

export interface PipelineExecutionPipelineRunFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step;
  error: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  processId: number;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent_step;
}

export type PipelineExecutionPipelineRunFragment_logs_nodes = PipelineExecutionPipelineRunFragment_logs_nodes_LogMessageEvent | PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepFailureEvent | PipelineExecutionPipelineRunFragment_logs_nodes_PipelineProcessStartedEvent | PipelineExecutionPipelineRunFragment_logs_nodes_ExecutionStepStartEvent;

export interface PipelineExecutionPipelineRunFragment_logs {
  __typename: "LogMessageConnection";
  nodes: PipelineExecutionPipelineRunFragment_logs_nodes[];
}

export interface PipelineExecutionPipelineRunFragment_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineExecutionPipelineRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineExecutionPipelineRunFragment_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineExecutionPipelineRunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineExecutionPipelineRunFragment_executionPlan_steps[];
}

export interface PipelineExecutionPipelineRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineExecutionPipelineRunFragment_logs;
  executionPlan: PipelineExecutionPipelineRunFragment_executionPlan;
}
