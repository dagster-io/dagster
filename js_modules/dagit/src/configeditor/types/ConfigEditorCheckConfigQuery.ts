/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ExecutionSelector, EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ConfigEditorCheckConfigQuery
// ====================================================

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid" | "PipelineNotFoundError";
}

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
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
  __typename: "EvaluationStack";
  entries: ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_stack_entries[];
}

export interface ConfigEditorCheckConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "MissingFieldConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
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
