/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunFragment
// ====================================================

export interface PipelineRunFragment_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunFragment_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunFragment_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunFragment_logs_nodes_StepMaterializationEvent_step | null;
  fileLocation: string;
  fileName: string;
}

export type PipelineRunFragment_logs_nodes = PipelineRunFragment_logs_nodes_LogMessageEvent | PipelineRunFragment_logs_nodes_ExecutionStepFailureEvent | PipelineRunFragment_logs_nodes_PipelineProcessStartedEvent | PipelineRunFragment_logs_nodes_StepMaterializationEvent;

export interface PipelineRunFragment_logs {
  __typename: "LogMessageConnection";
  nodes: PipelineRunFragment_logs_nodes[];
}

export interface PipelineRunFragment_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineRunFragment_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineRunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunFragment_executionPlan_steps[];
}

export interface PipelineRunFragment {
  __typename: "PipelineRun";
  logs: PipelineRunFragment_logs;
  executionPlan: PipelineRunFragment_executionPlan;
}
