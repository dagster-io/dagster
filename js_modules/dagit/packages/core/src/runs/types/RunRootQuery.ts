// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepKind, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunRootQuery
// ====================================================

export interface RunRootQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface RunRootQuery_pipelineRunOrError_Run_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
  solidSelection: string[] | null;
}

export interface RunRootQuery_pipelineRunOrError_Run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn_outputs_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn_outputs_type;
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  outputs: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn_outputs[];
  kind: StepKind;
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn[];
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  inputs: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs[];
  kind: StepKind;
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan {
  __typename: "ExecutionPlan";
  steps: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps[];
  artifactsPersisted: boolean;
}

export interface RunRootQuery_pipelineRunOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunRootQuery_pipelineRunOrError_Run_stats_PythonError {
  __typename: "PythonError";
}

export interface RunRootQuery_pipelineRunOrError_Run_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  endTime: number | null;
  startTime: number | null;
}

export type RunRootQuery_pipelineRunOrError_Run_stats = RunRootQuery_pipelineRunOrError_Run_stats_PythonError | RunRootQuery_pipelineRunOrError_Run_stats_RunStatsSnapshot;

export interface RunRootQuery_pipelineRunOrError_Run_stepStats_attempts {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunRootQuery_pipelineRunOrError_Run_stepStats_markers {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunRootQuery_pipelineRunOrError_Run_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  status: StepEventStatus | null;
  startTime: number | null;
  endTime: number | null;
  attempts: RunRootQuery_pipelineRunOrError_Run_stepStats_attempts[];
  markers: RunRootQuery_pipelineRunOrError_Run_stepStats_markers[];
}

export interface RunRootQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  pipeline: RunRootQuery_pipelineRunOrError_Run_pipeline;
  runConfig: any;
  runId: string;
  canTerminate: boolean;
  status: RunStatus;
  mode: string;
  tags: RunRootQuery_pipelineRunOrError_Run_tags[];
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  executionPlan: RunRootQuery_pipelineRunOrError_Run_executionPlan | null;
  stepKeysToExecute: string[] | null;
  repositoryOrigin: RunRootQuery_pipelineRunOrError_Run_repositoryOrigin | null;
  stats: RunRootQuery_pipelineRunOrError_Run_stats;
  stepStats: RunRootQuery_pipelineRunOrError_Run_stepStats[];
}

export type RunRootQuery_pipelineRunOrError = RunRootQuery_pipelineRunOrError_RunNotFoundError | RunRootQuery_pipelineRunOrError_Run;

export interface RunRootQuery {
  pipelineRunOrError: RunRootQuery_pipelineRunOrError;
}

export interface RunRootQueryVariables {
  runId: string;
}
