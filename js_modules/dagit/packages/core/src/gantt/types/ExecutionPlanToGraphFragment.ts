// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ExecutionPlanToGraphFragment
// ====================================================

export interface ExecutionPlanToGraphFragment_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
}

export interface ExecutionPlanToGraphFragment_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: ExecutionPlanToGraphFragment_steps_inputs_dependsOn_outputs_type;
}

export interface ExecutionPlanToGraphFragment_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  outputs: ExecutionPlanToGraphFragment_steps_inputs_dependsOn_outputs[];
}

export interface ExecutionPlanToGraphFragment_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: ExecutionPlanToGraphFragment_steps_inputs_dependsOn[];
}

export interface ExecutionPlanToGraphFragment_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: ExecutionPlanToGraphFragment_steps_inputs[];
}

export interface ExecutionPlanToGraphFragment {
  __typename: "ExecutionPlan";
  steps: ExecutionPlanToGraphFragment_steps[];
  artifactsPersisted: boolean;
}
