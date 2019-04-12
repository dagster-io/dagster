/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionSelector, EvaluationErrorReason, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PreviewConfigQuery
// ====================================================

export interface PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries = PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackPathEntry | PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries_EvaluationStackListItemEntry;

export interface PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack {
  __typename: "EvaluationStack";
  entries: PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack_entries[];
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors_stack;
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid_errors[];
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry_field {
  __typename: "ConfigTypeField";
  name: string;
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry {
  __typename: "EvaluationStackPathEntry";
  field: PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry_field;
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackListItemEntry {
  __typename: "EvaluationStackListItemEntry";
  listIndex: number;
}

export type PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries = PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackPathEntry | PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries_EvaluationStackListItemEntry;

export interface PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack {
  __typename: "EvaluationStack";
  entries: PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack_entries[];
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
  stack: PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors_stack;
}

export interface PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError {
  __typename: "PipelineConfigEvaluationError";
  errors: PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError_errors[];
}

export interface PreviewConfigQuery_executionPlan_ExecutionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PreviewConfigQuery_executionPlan_ExecutionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PreviewConfigQuery_executionPlan_ExecutionPlan_steps_solid;
  kind: StepKind;
}

export interface PreviewConfigQuery_executionPlan_ExecutionPlan {
  __typename: "ExecutionPlan";
  steps: PreviewConfigQuery_executionPlan_ExecutionPlan_steps[];
}

export interface PreviewConfigQuery_executionPlan_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export type PreviewConfigQuery_executionPlan = PreviewConfigQuery_executionPlan_PipelineConfigValidationInvalid | PreviewConfigQuery_executionPlan_PipelineConfigEvaluationError | PreviewConfigQuery_executionPlan_ExecutionPlan | PreviewConfigQuery_executionPlan_PipelineNotFoundError;

export interface PreviewConfigQuery {
  executionPlan: PreviewConfigQuery_executionPlan;
}

export interface PreviewConfigQueryVariables {
  pipeline: ExecutionSelector;
  config: any;
}
