

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigEditorCheckConfigQuery
// ====================================================

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid" | "PipelineNotFoundError";
}

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field {
  name: string;
}

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries = ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry | ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry;

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack {
  entries: ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries[];
}

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors {
  reason: EvaluationErrorReason;
  message: string;
  stack: ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack;
}

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors[];
}

export type ConfigEditorCheckConfigQuery_isPipelineConfigValid = ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid | ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid;

export interface ConfigEditorCheckConfigQuery {
  isPipelineConfigValid: ConfigEditorCheckConfigQuery_isPipelineConfigValid;
}

export interface ConfigEditorCheckConfigQueryVariables {
  pipeline: ExecutionSelector;
  config: any;
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
 * This type represents the fields necessary to identify a
 *         pipeline or pipeline subset.
 */
export interface ExecutionSelector {
  name: string;
  solidSubset?: string[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================