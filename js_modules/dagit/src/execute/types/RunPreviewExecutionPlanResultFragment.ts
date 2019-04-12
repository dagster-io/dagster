/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { StepKind, EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPreviewExecutionPlanResultFragment
// ====================================================

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_solid;
  kind: StepKind;
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan {
  __typename: "ExecutionPlan";
  steps: RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps[];
}

export interface RunPreviewExecutionPlanResultFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface RunPreviewExecutionPlanResultFragment_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
}

export interface RunPreviewExecutionPlanResultFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: RunPreviewExecutionPlanResultFragment_PipelineConfigValidationInvalid_errors[];
}

export interface RunPreviewExecutionPlanResultFragment_PipelineConfigEvaluationError_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
}

export interface RunPreviewExecutionPlanResultFragment_PipelineConfigEvaluationError {
  __typename: "PipelineConfigEvaluationError";
  errors: RunPreviewExecutionPlanResultFragment_PipelineConfigEvaluationError_errors[];
}

export type RunPreviewExecutionPlanResultFragment = RunPreviewExecutionPlanResultFragment_ExecutionPlan | RunPreviewExecutionPlanResultFragment_PipelineNotFoundError | RunPreviewExecutionPlanResultFragment_PipelineConfigValidationInvalid | RunPreviewExecutionPlanResultFragment_PipelineConfigEvaluationError;
