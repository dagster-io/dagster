// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: GanttChartExecutionPlanFragment
// ====================================================

export interface GanttChartExecutionPlanFragment_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
}

export interface GanttChartExecutionPlanFragment_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: GanttChartExecutionPlanFragment_steps_inputs_dependsOn_outputs_type;
}

export interface GanttChartExecutionPlanFragment_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: GanttChartExecutionPlanFragment_steps_inputs_dependsOn_outputs[];
}

export interface GanttChartExecutionPlanFragment_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: GanttChartExecutionPlanFragment_steps_inputs_dependsOn[];
}

export interface GanttChartExecutionPlanFragment_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: GanttChartExecutionPlanFragment_steps_inputs[];
}

export interface GanttChartExecutionPlanFragment {
  __typename: "ExecutionPlan";
  steps: GanttChartExecutionPlanFragment_steps[];
  artifactsPersisted: boolean;
}
