/* tslint:disable */
// This file was automatically generated and should not be edited.

import { StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPreviewExecutionPlanFragment
// ====================================================

export interface RunPreviewExecutionPlanFragment_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface RunPreviewExecutionPlanFragment_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: RunPreviewExecutionPlanFragment_steps_solid;
  kind: StepKind;
}

export interface RunPreviewExecutionPlanFragment {
  __typename: "ExecutionPlan";
  steps: RunPreviewExecutionPlanFragment_steps[];
}
