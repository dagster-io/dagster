// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, StepKind } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunFragment
// ====================================================

export interface RunFragment_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
  solidSelection: string[] | null;
}

export interface RunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
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
  kind: StepKind;
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

export interface RunFragment_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunFragment_stats_PythonError {
  __typename: "PythonError";
}

export interface RunFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
  startTime: number | null;
}

export type RunFragment_stats = RunFragment_stats_PythonError | RunFragment_stats_PipelineRunStatsSnapshot;

export interface RunFragment {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
  pipeline: RunFragment_pipeline;
  runConfigYaml: string;
  canTerminate: boolean;
  mode: string;
  tags: RunFragment_tags[];
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  executionPlan: RunFragment_executionPlan | null;
  stepKeysToExecute: string[] | null;
  repositoryOrigin: RunFragment_repositoryOrigin | null;
  stats: RunFragment_stats;
}
