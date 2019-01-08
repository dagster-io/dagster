

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: PipelineExecutionCodeEditorFragment
// ====================================================

export interface PipelineExecutionCodeEditorFragment_environmentType {
  name: string;
}

export interface PipelineExecutionCodeEditorFragment_types_RegularType {
  __typename: "RegularType";
  name: string;
}

export interface PipelineExecutionCodeEditorFragment_types_CompositeType_fields_type {
  name: string;
}

export interface PipelineExecutionCodeEditorFragment_types_CompositeType_fields {
  name: string;
  type: PipelineExecutionCodeEditorFragment_types_CompositeType_fields_type;
}

export interface PipelineExecutionCodeEditorFragment_types_CompositeType {
  __typename: "CompositeType";
  name: string;
  fields: PipelineExecutionCodeEditorFragment_types_CompositeType_fields[];
}

export type PipelineExecutionCodeEditorFragment_types = PipelineExecutionCodeEditorFragment_types_RegularType | PipelineExecutionCodeEditorFragment_types_CompositeType;

export interface PipelineExecutionCodeEditorFragment {
  name: string;
  environmentType: PipelineExecutionCodeEditorFragment_environmentType;
  types: PipelineExecutionCodeEditorFragment_types[];
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