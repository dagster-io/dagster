/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ConfigEditorPlanValidationFragment
// ====================================================

export interface ConfigEditorPlanValidationFragment_ExecutionPlan {
  __typename: "ExecutionPlan" | "PipelineNotFoundError";
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries = ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry | ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry;

export interface ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack {
  __typename: "EvaluationStack";
  entries: ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack_entries[];
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors_stack;
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid_errors[];
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries = ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry | ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackListItemEntry;

export interface ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack {
  __typename: "EvaluationStack";
  entries: ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack_entries[];
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors_stack;
}

export interface ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError {
  __typename: "PipelineConfigEvaluationError";
  errors: ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError_errors[];
}

export type ConfigEditorPlanValidationFragment = ConfigEditorPlanValidationFragment_ExecutionPlan | ConfigEditorPlanValidationFragment_PipelineConfigValidationInvalid | ConfigEditorPlanValidationFragment_PipelineConfigEvaluationError;
