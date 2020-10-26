// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: GaantChartExecutionPlanFragment
// ====================================================

export interface GaantChartExecutionPlanFragment_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
}

export interface GaantChartExecutionPlanFragment_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: GaantChartExecutionPlanFragment_steps_inputs_dependsOn_outputs_type;
}

export interface GaantChartExecutionPlanFragment_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: GaantChartExecutionPlanFragment_steps_inputs_dependsOn_outputs[];
}

export interface GaantChartExecutionPlanFragment_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: GaantChartExecutionPlanFragment_steps_inputs_dependsOn[];
}

export interface GaantChartExecutionPlanFragment_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: GaantChartExecutionPlanFragment_steps_inputs[];
}

export interface GaantChartExecutionPlanFragment {
  __typename: "ExecutionPlan";
  steps: GaantChartExecutionPlanFragment_steps[];
  artifactsPersisted: boolean;
}
