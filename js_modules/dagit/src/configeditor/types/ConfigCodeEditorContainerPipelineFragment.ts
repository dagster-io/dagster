/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: ConfigEditorContainerPipelineFragment
// ====================================================

export interface ConfigEditorContainerPipelineFragment_types_RegularType {
  __typename: "RegularType";
  name: string;
}

export interface ConfigEditorContainerPipelineFragment_types_CompositeType_fields_type {
  name: string;
}

export interface ConfigEditorContainerPipelineFragment_types_CompositeType_fields {
  name: string;
  type: ConfigEditorContainerPipelineFragment_types_CompositeType_fields_type;
}

export interface ConfigEditorContainerPipelineFragment_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  fields: ConfigEditorContainerPipelineFragment_types_CompositeType_fields[];
}

export type ConfigEditorContainerPipelineFragment_types =
  | ConfigEditorContainerPipelineFragment_types_RegularType
  | ConfigEditorContainerPipelineFragment_types_CompositeType;

export interface ConfigEditorContainerPipelineFragment {
  name: string;
  types: ConfigEditorContainerPipelineFragment_types[];
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
