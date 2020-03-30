// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPreviewConfigValidationFragment
// ====================================================

export interface RunPreviewConfigValidationFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError" | "PipelineConfigValidationValid" | "PipelineNotFoundError" | "PythonError";
}

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
}

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export type RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries = RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry | RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry;

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack {
  __typename: "EvaluationStack";
  entries: RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries[];
}

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors_stack;
}

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors[];
}

export type RunPreviewConfigValidationFragment = RunPreviewConfigValidationFragment_InvalidSubsetError | RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid;
