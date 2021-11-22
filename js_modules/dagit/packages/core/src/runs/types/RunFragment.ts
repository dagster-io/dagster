/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepKind, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunFragment
// ====================================================

export interface RunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunFragment_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
  solidSelection: string[] | null;
}

export interface RunFragment_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
}

export interface RunFragment_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunFragment_executionPlan_steps_inputs_dependsOn[];
}

export interface RunFragment_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: RunFragment_executionPlan_steps_inputs[];
}

export interface RunFragment_executionPlan {
  __typename: "ExecutionPlan";
  artifactsPersisted: boolean;
  steps: RunFragment_executionPlan_steps[];
}

export interface RunFragment_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunFragment_stats_PythonError {
  __typename: "PythonError";
}

export interface RunFragment_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  endTime: number | null;
  startTime: number | null;
}

export type RunFragment_stats = RunFragment_stats_PythonError | RunFragment_stats_RunStatsSnapshot;

export interface RunFragment_stepStats_attempts {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunFragment_stepStats_markers {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunFragment_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  status: StepEventStatus | null;
  startTime: number | null;
  endTime: number | null;
  attempts: RunFragment_stepStats_attempts[];
  markers: RunFragment_stepStats_markers[];
}

export interface RunFragment {
  __typename: "Run";
  id: string;
  runConfig: any;
  runId: string;
  canTerminate: boolean;
  status: RunStatus;
  mode: string;
  tags: RunFragment_tags[];
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineName: string;
  pipeline: RunFragment_pipeline;
  pipelineSnapshotId: string | null;
  executionPlan: RunFragment_executionPlan | null;
  stepKeysToExecute: string[] | null;
  repositoryOrigin: RunFragment_repositoryOrigin | null;
  stats: RunFragment_stats;
  stepStats: RunFragment_stepStats[];
}
