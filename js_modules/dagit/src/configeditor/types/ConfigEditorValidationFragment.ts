/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ConfigEditorValidationFragment
// ====================================================

export interface ConfigEditorValidationFragment_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid" | "PipelineNotFoundError";
}

export interface ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries = ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry | ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry;

export interface ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack {
  __typename: "EvaluationStack";
  entries: ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries[];
}

export interface ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors_stack;
}

export interface ConfigEditorValidationFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: ConfigEditorValidationFragment_PipelineConfigValidationInvalid_errors[];
}

export type ConfigEditorValidationFragment = ConfigEditorValidationFragment_PipelineConfigValidationValid | ConfigEditorValidationFragment_PipelineConfigValidationInvalid;
