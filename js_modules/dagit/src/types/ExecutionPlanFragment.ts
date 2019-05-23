// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { StepKind } from "./globalTypes";

// ====================================================
// GraphQL fragment: ExecutionPlanFragment
// ====================================================

export interface ExecutionPlanFragment_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
}

export interface ExecutionPlanFragment {
  __typename: "ExecutionPlan";
  steps: ExecutionPlanFragment_steps[];
  artifactsPersisted: boolean;
}
