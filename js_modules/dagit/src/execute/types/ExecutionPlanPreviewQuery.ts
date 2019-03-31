/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ExecutionSelector, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ExecutionPlanPreviewQuery
// ====================================================

export interface ExecutionPlanPreviewQuery_executionPlan_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
}

export interface ExecutionPlanPreviewQuery_executionPlan_ExecutionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface ExecutionPlanPreviewQuery_executionPlan_ExecutionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: ExecutionPlanPreviewQuery_executionPlan_ExecutionPlan_steps_solid;
  kind: StepKind;
}

export interface ExecutionPlanPreviewQuery_executionPlan_ExecutionPlan {
  __typename: "ExecutionPlan";
  steps: ExecutionPlanPreviewQuery_executionPlan_ExecutionPlan_steps[];
}

export interface ExecutionPlanPreviewQuery_executionPlan_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export type ExecutionPlanPreviewQuery_executionPlan = ExecutionPlanPreviewQuery_executionPlan_PipelineConfigValidationInvalid | ExecutionPlanPreviewQuery_executionPlan_ExecutionPlan | ExecutionPlanPreviewQuery_executionPlan_PipelineNotFoundError;

export interface ExecutionPlanPreviewQuery {
  executionPlan: ExecutionPlanPreviewQuery_executionPlan;
}

export interface ExecutionPlanPreviewQueryVariables {
  pipeline: ExecutionSelector;
  config: any;
}
