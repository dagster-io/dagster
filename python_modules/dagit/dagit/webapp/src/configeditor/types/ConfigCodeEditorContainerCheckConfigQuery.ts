

/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigCodeEditorContainerCheckConfigQuery
// ====================================================

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid" | "PipelineNotFoundError";
}

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field {
  name: string;
}

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries = ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry | ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry;

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack {
  entries: ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries[];
}

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors {
  message: string;
  stack: ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack;
}

export interface ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors[];
}

export type ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid = ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid | ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid;

export interface ConfigCodeEditorContainerCheckConfigQuery {
  isPipelineConfigValid: ConfigCodeEditorContainerCheckConfigQuery_isPipelineConfigValid;
}

export interface ConfigCodeEditorContainerCheckConfigQueryVariables {
  executionParams: PipelineExecutionParams;
}

/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

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
  JOIN = "JOIN",
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