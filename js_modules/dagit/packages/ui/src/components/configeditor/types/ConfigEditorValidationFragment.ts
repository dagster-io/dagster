/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../../../../../../../../src/types/globalTypes";

// ====================================================
// GraphQL fragment: ConfigEditorValidationFragment
// ====================================================

export interface ConfigEditorValidationFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError" | "PipelineConfigValidationValid" | "PipelineNotFoundError" | "PythonError";
}

export interface ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export interface ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackMapKeyEntry {
  __typename: "EvaluationStackMapKeyEntry";
  mapKey: any;
}

export interface ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackMapValueEntry {
  __typename: "EvaluationStackMapValueEntry";
  mapKey: any;
}

export type ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries = ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry | ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry | ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackMapKeyEntry | ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries_EvaluationStackMapValueEntry;

export interface ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack {
  __typename: "EvaluationStack";
  entries: ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack_entries[];
}

export interface ConfigEditorValidationFragment_RunConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: ConfigEditorValidationFragment_RunConfigValidationInvalid_errors_stack;
}

export interface ConfigEditorValidationFragment_RunConfigValidationInvalid {
  __typename: "RunConfigValidationInvalid";
  errors: ConfigEditorValidationFragment_RunConfigValidationInvalid_errors[];
}

export type ConfigEditorValidationFragment = ConfigEditorValidationFragment_InvalidSubsetError | ConfigEditorValidationFragment_RunConfigValidationInvalid;
