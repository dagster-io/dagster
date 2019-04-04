/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PipelineRunRootQuery
// ====================================================

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError";
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent_step | null;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_step | null;
  error: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent_error;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent_step | null;
  fileLocation: string;
  fileName: string;
}

export type PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes = PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_LogMessageEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineInitFailureEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_ExecutionStepFailureEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_PipelineProcessStartedEvent | PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes_StepMaterializationEvent;

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs {
  __typename: "LogMessageConnection";
  pageInfo: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_pageInfo;
  nodes: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs_nodes[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps[];
}

export interface PipelineRunRootQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  logs: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_logs;
  executionPlan: PipelineRunRootQuery_pipelineRunOrError_PipelineRun_executionPlan;
}

export type PipelineRunRootQuery_pipelineRunOrError = PipelineRunRootQuery_pipelineRunOrError_PipelineRunNotFoundError | PipelineRunRootQuery_pipelineRunOrError_PipelineRun;

export interface PipelineRunRootQuery {
  pipelineRunOrError: PipelineRunRootQuery_pipelineRunOrError;
}

export interface PipelineRunRootQueryVariables {
  runId: string;
}
