/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ExecutionSelector, PipelineRunStatus, LogLevel, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartPipelineExecution
// ====================================================

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_LogMessageEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_LogMessageEvent_step | null;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_step | null;
  error: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_StepMaterializationEvent_step | null;
  fileLocation: string;
  fileName: string;
}

export type StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes = StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_LogMessageEvent | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_PipelineProcessStartedEvent | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_StepMaterializationEvent;

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_pageInfo {
  __typename: "PageInfo";
  lastCursor: any | null;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs {
  __typename: "LogMessageConnection";
  nodes: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes[];
  pageInfo: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_pageInfo;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps_solid;
  kind: StepKind;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan {
  __typename: "ExecutionPlan";
  steps: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps[];
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  logs: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs;
  executionPlan: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess {
  __typename: "StartPipelineExecutionSuccess";
  run: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "MissingFieldConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid_errors[];
}

export type StartPipelineExecution_startPipelineExecution = StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess | StartPipelineExecution_startPipelineExecution_PipelineNotFoundError | StartPipelineExecution_startPipelineExecution_PipelineConfigValidationInvalid;

export interface StartPipelineExecution {
  startPipelineExecution: StartPipelineExecution_startPipelineExecution;
}

export interface StartPipelineExecutionVariables {
  pipeline: ExecutionSelector;
  config: any;
}
