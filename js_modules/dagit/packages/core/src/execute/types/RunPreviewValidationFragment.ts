// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPreviewValidationFragment
// ====================================================

export interface RunPreviewValidationFragment_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid";
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack_entries = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack_entries_EvaluationStackPathEntry | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack_entries_EvaluationStackListItemEntry;

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack {
  __typename: "EvaluationStack";
  entries: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack_entries[];
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError {
  __typename: "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError_stack;
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
  __typename: "FieldNotDefinedConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError_stack;
  fieldName: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  fieldName: string;
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack_entries = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack_entries_EvaluationStackPathEntry | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack_entries_EvaluationStackListItemEntry;

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack {
  __typename: "EvaluationStack";
  entries: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack_entries[];
}

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError {
  __typename: "FieldsNotDefinedConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError_stack;
  fieldNames: string[];
}

export type RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_RuntimeMismatchConfigError | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldConfigError | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_MissingFieldsConfigError | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldNotDefinedConfigError | RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors_FieldsNotDefinedConfigError;

export interface RunPreviewValidationFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors[];
}

export interface RunPreviewValidationFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface RunPreviewValidationFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export interface RunPreviewValidationFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunPreviewValidationFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunPreviewValidationFragment_PythonError_cause | null;
}

export type RunPreviewValidationFragment = RunPreviewValidationFragment_PipelineConfigValidationValid | RunPreviewValidationFragment_PipelineConfigValidationInvalid | RunPreviewValidationFragment_PipelineNotFoundError | RunPreviewValidationFragment_InvalidSubsetError | RunPreviewValidationFragment_PythonError;
