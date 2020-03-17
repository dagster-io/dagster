// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum ComputeIOType {
  STDERR = "STDERR",
  STDOUT = "STDOUT",
}

export enum EvaluationErrorReason {
  FIELDS_NOT_DEFINED = "FIELDS_NOT_DEFINED",
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
  MISSING_REQUIRED_FIELDS = "MISSING_REQUIRED_FIELDS",
  RUNTIME_TYPE_MISMATCH = "RUNTIME_TYPE_MISMATCH",
  SELECTOR_FIELD_ERROR = "SELECTOR_FIELD_ERROR",
}

export enum LogLevel {
  CRITICAL = "CRITICAL",
  DEBUG = "DEBUG",
  ERROR = "ERROR",
  INFO = "INFO",
  WARNING = "WARNING",
}

export enum ObjectStoreOperationType {
  CP_OBJECT = "CP_OBJECT",
  GET_OBJECT = "GET_OBJECT",
  RM_OBJECT = "RM_OBJECT",
  SET_OBJECT = "SET_OBJECT",
}

export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  MANAGED = "MANAGED",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum ScheduleAttemptStatus {
  ERROR = "ERROR",
  SKIPPED = "SKIPPED",
  SUCCESS = "SUCCESS",
}

export enum ScheduleStatus {
  ENDED = "ENDED",
  RUNNING = "RUNNING",
  STOPPED = "STOPPED",
}

export enum ScheduleTickStatus {
  FAILURE = "FAILURE",
  SKIPPED = "SKIPPED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS",
}

export enum StepKind {
  COMPUTE = "COMPUTE",
}

export interface ExecutionMetadata {
  runId?: string | null;
  tags?: ExecutionTag[] | null;
}

export interface ExecutionParams {
  selector: ExecutionSelector;
  environmentConfigData?: any | null;
  mode?: string | null;
  executionMetadata?: ExecutionMetadata | null;
  stepKeys?: string[] | null;
  preset?: string | null;
  retryRunId?: string | null;
}

export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

export interface ExecutionTag {
  key: string;
  value: string;
}

export interface PipelineRunsFilter {
  runId?: string | null;
  pipelineName?: string | null;
  tags?: ExecutionTag[] | null;
  status?: PipelineRunStatus | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
