

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeListContainerQuery
// ====================================================

export interface TypeListContainerQuery_pipelineOrError_PythonError {
  __typename: "PythonError" | "PipelineNotFoundError";
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline_types_typeAttributes {
  /**
   * 
   * True if the system defines it and it is the same type across pipelines.
   * Examples include "Int" and "String."
   */
  isBuiltin: boolean;
  /**
   * 
   * Dagster generates types for base elements of the config system (e.g. the solids and
   * context field of the base environment). These types are always present
   * and are typically not relevant to an end user. This flag allows tool authors to
   * filter out those types by default.
   * 
   */
  isSystemConfig: boolean;
  isNamed: boolean;
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline_types {
  name: string;
  typeAttributes: TypeListContainerQuery_pipelineOrError_Pipeline_types_typeAttributes;
  description: string | null;
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  types: TypeListContainerQuery_pipelineOrError_Pipeline_types[];
}

export type TypeListContainerQuery_pipelineOrError = TypeListContainerQuery_pipelineOrError_PythonError | TypeListContainerQuery_pipelineOrError_Pipeline;

export interface TypeListContainerQuery {
  pipelineOrError: TypeListContainerQuery_pipelineOrError;
}

export interface TypeListContainerQueryVariables {
  pipelineName: string;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum EvaluationErrorReason {
  FIELD_NOT_DEFINED = "FIELD_NOT_DEFINED",
  MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD",
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