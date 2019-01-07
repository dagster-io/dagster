

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: StartPipelineExecution
// ====================================================

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_LogMessageEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent";
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_step {
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_error {
  stack: string[];
  message: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepFailureEvent";
  step: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_step;
  error: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent_error;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_PipelineProcessStartedEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "PipelineProcessStartedEvent";
  processId: number;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepStartEvent_step {
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepStartEvent {
  message: string;
  timestamp: string;
  level: LogLevel;
  __typename: "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent";
  step: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepStartEvent_step;
}

export type StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes = StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_LogMessageEvent | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepFailureEvent | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_PipelineProcessStartedEvent | StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes_ExecutionStepStartEvent;

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_pageInfo {
  lastCursor: any | null;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs {
  nodes: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_nodes[];
  pageInfo: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_logs_pageInfo;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps_solid {
  name: string;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps {
  name: string;
  solid: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps_solid;
  tag: StepTag;
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan {
  steps: StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run_executionPlan_steps[];
}

export interface StartPipelineExecution_startPipelineExecution_StartPipelineExecutionSuccess_run {
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
  executionParams: PipelineExecutionParams;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM",
}

/**
 * 
 */
export interface PipelineExecutionParams {
  pipelineName: string;
  config?: any | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================