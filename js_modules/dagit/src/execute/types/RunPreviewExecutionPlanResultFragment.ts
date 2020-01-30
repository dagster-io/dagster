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

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs_dependsOn_outputs[];
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs_dependsOn[];
}

export interface RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: RunPreviewExecutionPlanResultFragment_ExecutionPlan_steps_inputs[];
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

export interface RunPreviewExecutionPlanResultFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunPreviewExecutionPlanResultFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunPreviewExecutionPlanResultFragment_PythonError_cause | null;
}

export type RunPreviewExecutionPlanResultFragment = RunPreviewExecutionPlanResultFragment_PipelineConfigValidationInvalid | RunPreviewExecutionPlanResultFragment_ExecutionPlan | RunPreviewExecutionPlanResultFragment_PipelineNotFoundError | RunPreviewExecutionPlanResultFragment_InvalidSubsetError | RunPreviewExecutionPlanResultFragment_PythonError;
