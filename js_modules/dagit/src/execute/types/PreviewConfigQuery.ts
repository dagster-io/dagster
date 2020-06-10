// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineSelector, EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PreviewConfigQuery
// ====================================================

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid";
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries = PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackPathEntry | PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries_EvaluationStackListItemEntry;

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack {
  __typename: "EvaluationStack";
  entries: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack_entries[];
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries = PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackPathEntry | PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries_EvaluationStackListItemEntry;

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack {
  __typename: "EvaluationStack";
  entries: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack_entries[];
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError {
  __typename: "MissingFieldConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_stack;
  field: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError_field;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries = PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackPathEntry | PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries_EvaluationStackListItemEntry;

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack {
  __typename: "EvaluationStack";
  entries: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack_entries[];
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_fields {
  __typename: "ConfigTypeField";
  name: string;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError {
  __typename: "MissingFieldsConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_stack;
  fields: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError_fields[];
}

export type PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors = PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError | PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldConfigError | PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError;

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid_errors[];
}

export interface PreviewConfigQuery_isPipelineConfigValid_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface PreviewConfigQuery_isPipelineConfigValid_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export interface PreviewConfigQuery_isPipelineConfigValid_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PreviewConfigQuery_isPipelineConfigValid_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PreviewConfigQuery_isPipelineConfigValid_PythonError_cause | null;
}

export type PreviewConfigQuery_isPipelineConfigValid = PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationValid | PreviewConfigQuery_isPipelineConfigValid_PipelineConfigValidationInvalid | PreviewConfigQuery_isPipelineConfigValid_PipelineNotFoundError | PreviewConfigQuery_isPipelineConfigValid_InvalidSubsetError | PreviewConfigQuery_isPipelineConfigValid_PythonError;

export interface PreviewConfigQuery {
  isPipelineConfigValid: PreviewConfigQuery_isPipelineConfigValid;
}

export interface PreviewConfigQueryVariables {
  pipeline: PipelineSelector;
  runConfigData: any;
  mode: string;
}
