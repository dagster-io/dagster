// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunFragment
// ====================================================

export interface RunFragment_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
}

export interface RunFragment_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunFragment_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunFragment_pipeline_Pipeline_solids[];
}

export type RunFragment_pipeline = RunFragment_pipeline_UnknownPipeline | RunFragment_pipeline_Pipeline;

export interface RunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: RunFragment_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: RunFragment_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface RunFragment_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunFragment_executionPlan_steps_inputs_dependsOn[];
}

export interface RunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  inputs: RunFragment_executionPlan_steps_inputs[];
  kind: StepKind;
}

export interface RunFragment_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunFragment_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface RunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  pipeline: RunFragment_pipeline;
  environmentConfigYaml: string;
  canCancel: boolean;
  mode: string;
  tags: RunFragment_tags[];
  executionPlan: RunFragment_executionPlan | null;
  stepKeysToExecute: string[] | null;
}
