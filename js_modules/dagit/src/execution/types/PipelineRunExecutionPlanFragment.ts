/* tslint:disable */
// This file was automatically generated and should not be edited.

import { StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunExecutionPlanFragment
// ====================================================

export interface PipelineRunExecutionPlanFragment_executionPlan_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface PipelineRunExecutionPlanFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: PipelineRunExecutionPlanFragment_executionPlan_steps_solid;
  kind: StepKind;
}

export interface PipelineRunExecutionPlanFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: PipelineRunExecutionPlanFragment_executionPlan_steps[];
}

export interface PipelineRunExecutionPlanFragment {
  __typename: "PipelineRun";
  executionPlan: PipelineRunExecutionPlanFragment_executionPlan;
}
