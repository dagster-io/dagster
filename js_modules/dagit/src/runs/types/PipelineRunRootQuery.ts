/* tslint:disable */
// This file was automatically generated and should not be edited.

import { LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunRootQuery
// ====================================================

export interface PipelineRunRootQuery_pipelineRun_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRun_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRun_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunRootQuery_pipelineRun_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRun_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRun_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRun_logs_nodes_StepMaterializationEvent_step | null;
  fileLocation: string;
  fileName: string;
}

export type PipelineRunRootQuery_pipelineRun_logs_nodes = PipelineRunRootQuery_pipelineRun_logs_nodes_LogMessageEvent | PipelineRunRootQuery_pipelineRun_logs_nodes_ExecutionStepFailureEvent | PipelineRunRootQuery_pipelineRun_logs_nodes_PipelineProcessStartedEvent | PipelineRunRootQuery_pipelineRun_logs_nodes_StepMaterializationEvent;

export interface PipelineRunRootQuery_pipelineRun_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunRootQuery_pipelineRun_logs_pageInfo;
  nodes: PipelineRunRootQuery_pipelineRun_logs_nodes[];
}

export interface PipelineRunRootQuery_pipelineRun_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRun_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineRunRootQuery_pipelineRun_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineRunRootQuery_pipelineRun_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunRootQuery_pipelineRun_executionPlan_steps[];
}

export interface PipelineRunRootQuery_pipelineRun {
  __typename: "PipelineRun";
  runId: string;
  logs: PipelineRunRootQuery_pipelineRun_logs;
  executionPlan: PipelineRunRootQuery_pipelineRun_executionPlan;
}

export interface PipelineRunRootQuery {
  pipelineRun: PipelineRunRootQuery_pipelineRun | null;
}

export interface PipelineRunRootQueryVariables {
  runId: string;
}
