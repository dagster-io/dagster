// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunRootQuery
// ====================================================

export interface RunRootQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_Pipeline_solids {
  __typename: "Solid";
  name: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_Pipeline {
  __typename: "Pipeline";
  name: string;
  solids: RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_Pipeline_solids[];
}

export type RunRootQuery_pipelineRunOrError_PipelineRun_pipeline = RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_UnknownPipeline | RunRootQuery_pipelineRunOrError_PipelineRun_pipeline_Pipeline;

export interface RunRootQuery_pipelineRunOrError_PipelineRun_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn_outputs[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs_dependsOn[];
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  inputs: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps_inputs[];
  kind: StepKind;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface RunRootQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  pipeline: RunRootQuery_pipelineRunOrError_PipelineRun_pipeline;
  runId: string;
  status: PipelineRunStatus;
  environmentConfigYaml: string;
  canCancel: boolean;
  mode: string;
  tags: RunRootQuery_pipelineRunOrError_PipelineRun_tags[];
  executionPlan: RunRootQuery_pipelineRunOrError_PipelineRun_executionPlan | null;
  stepKeysToExecute: string[] | null;
}

export type RunRootQuery_pipelineRunOrError = RunRootQuery_pipelineRunOrError_PipelineRunNotFoundError | RunRootQuery_pipelineRunOrError_PipelineRun;

export interface RunRootQuery {
  pipelineRunOrError: RunRootQuery_pipelineRunOrError;
}

export interface RunRootQueryVariables {
  runId: string;
}
