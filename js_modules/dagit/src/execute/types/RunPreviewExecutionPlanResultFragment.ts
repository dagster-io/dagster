// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPreviewExecutionPlanResultFragment
// ====================================================

export interface RunPreviewExecutionPlanResultFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan {
  __typename: "ExecutionPlan";
  steps: RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface RunPreviewExecutionPlanResultFragment_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface RunPreviewExecutionPlanResultFragment_InvalidSubsetError {
  __typename: "InvalidSubsetError";
  message: string;
}

export type RunPreviewExecutionPlanResultFragment = RunPreviewExecutionPlanResultFragment_PipelineConfigValidationInvalid | RunPreviewExecutionPlanResultFragment_ExecutionPlan | RunPreviewExecutionPlanResultFragment_PipelineNotFoundError | RunPreviewExecutionPlanResultFragment_InvalidSubsetError;
