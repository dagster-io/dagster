/* tslint:disable */
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ConfigEditorValidationInvalidFragment
// ====================================================

export interface ConfigEditorValidationInvalidFragment_errors_stack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface ConfigEditorValidationInvalidFragment_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: ConfigEditorValidationInvalidFragment_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface ConfigEditorValidationInvalidFragment_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type ConfigEditorValidationInvalidFragment_errors_stack_entries = ConfigEditorValidationInvalidFragment_errors_stack_entries_EvaluationStackPathEntry | ConfigEditorValidationInvalidFragment_errors_stack_entries_EvaluationStackListItemEntry;

export interface ConfigEditorValidationInvalidFragment_errors_stack {
  __typename: "EvaluationStack";
  entries: ConfigEditorValidationInvalidFragment_errors_stack_entries[];
}

export interface ConfigEditorValidationInvalidFragment_errors {
  __typename: "FieldNotDefinedConfigError" | "MissingFieldConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: ConfigEditorValidationInvalidFragment_errors_stack;
}

export interface ConfigEditorValidationInvalidFragment {
  __typename: "PipelineConfigValidationInvalid";
  errors: ConfigEditorValidationInvalidFragment_errors[];
}
