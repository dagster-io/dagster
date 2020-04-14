// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPreviewValidationFragment
// ====================================================

export interface RunPreviewValidationFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError" | "PipelineConfigValidationValid" | "PipelineNotFoundError" | "PythonError";
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackPathEntry | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackListItemEntry;

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack {
  __typename: "EvaluationStack";
  entries: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries[];
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackPathEntry | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackListItemEntry;

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack {
  __typename: "EvaluationStack";
  entries: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries[];
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError {
  __typename: "MissingFieldConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack;
  field: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_field;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackPathEntry | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackListItemEntry;

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack {
  __typename: "EvaluationStack";
  entries: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries[];
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_fields {
  __typename: "ConfigTypeField";
  name: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError {
  __typename: "MissingFieldsConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack;
  fields: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_fields[];
}

export type RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError;

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors[];
}

export type RunPreviewValidationFragment = RunPreviewValidationFragment_InvalidSubsetError | RunPreviewValidationFragment_PipelineConfigValidationInvalid;
