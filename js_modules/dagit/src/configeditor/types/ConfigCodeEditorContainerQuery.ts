/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigEditorContainerQuery
// ====================================================

export interface ConfigEditorContainerQuery_pipelineOrError_PythonError {
  __typename: "PythonError" | "PipelineNotFoundError";
}

export interface ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_RegularType {
  __typename: "RegularType";
  name: string;
}

export interface ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields_type {
  name: string;
}

export interface ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields {
  name: string;
  type: ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields_type;
}

export interface ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  fields: ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType_fields[];
}

export type ConfigEditorContainerQuery_pipelineOrError_Pipeline_types =
  | ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_RegularType
  | ConfigEditorContainerQuery_pipelineOrError_Pipeline_types_CompositeType;

export interface ConfigEditorContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  types: ConfigEditorContainerQuery_pipelineOrError_Pipeline_types[];
}

export type ConfigEditorContainerQuery_pipelineOrError =
  | ConfigEditorContainerQuery_pipelineOrError_PythonError
  | ConfigEditorContainerQuery_pipelineOrError_Pipeline;

export interface ConfigEditorContainerQuery {
  pipelineOrError: ConfigEditorContainerQuery_pipelineOrError;
}

export interface ConfigEditorContainerQueryVariables {
  pipelineName: string;
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
  WARNING = "WARNING"
}

/**
 * An enumeration.
 */
export enum PipelineRunStatus {
  FAILURE = "FAILURE",
  NOT_STARTED = "NOT_STARTED",
  STARTED = "STARTED",
  SUCCESS = "SUCCESS"
}

export enum StepTag {
  INPUT_EXPECTATION = "INPUT_EXPECTATION",
  INPUT_THUNK = "INPUT_THUNK",
  JOIN = "JOIN",
  MATERIALIZATION_THUNK = "MATERIALIZATION_THUNK",
  OUTPUT_EXPECTATION = "OUTPUT_EXPECTATION",
  SERIALIZE = "SERIALIZE",
  TRANSFORM = "TRANSFORM"
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
