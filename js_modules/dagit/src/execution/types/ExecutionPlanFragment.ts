/* tslint:disable */
// This file was automatically generated and should not be edited.

import { StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ExecutionPlanFragment
// ====================================================

export interface ExecutionPlanFragment_steps_solid {
  __typename: "Solid";
  name: string;
}

export interface ExecutionPlanFragment_steps {
  __typename: "ExecutionStep";
  name: string;
  solid: ExecutionPlanFragment_steps_solid;
  kind: StepKind;
}

export interface ExecutionPlanFragment {
  __typename: "ExecutionPlan";
  steps: ExecutionPlanFragment_steps[];
}
