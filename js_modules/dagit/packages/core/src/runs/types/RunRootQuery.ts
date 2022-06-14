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

export interface RunRootQuery_pipelineRunOrError_Run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunRootQuery_pipelineRunOrError_Run_assets_key {
  __typename: "AssetKey";
  path: string[];
}

export interface RunRootQuery_pipelineRunOrError_Run_assets {
  __typename: "MaterializedKey";
  id: string;
  key: RunRootQuery_pipelineRunOrError_Run_assets_key;
}

export interface RunRootQuery_pipelineRunOrError_Run_assetSelection {
  __typename: "AssetKey";
  path: string[];
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn[];
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps_inputs[];
}

export interface RunRootQuery_pipelineRunOrError_Run_executionPlan {
  __typename: "ExecutionPlan";
  artifactsPersisted: boolean;
  steps: RunRootQuery_pipelineRunOrError_Run_executionPlan_steps[];
}

export interface RunRootQuery_pipelineRunOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

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
  runConfig: any;
  runId: string;
  canTerminate: boolean;
  status: RunStatus;
  mode: string;
  tags: RunRootQuery_pipelineRunOrError_Run_tags[];
  assets: RunRootQuery_pipelineRunOrError_Run_assets[];
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  assetSelection: RunRootQuery_pipelineRunOrError_Run_assetSelection[] | null;
  pipelineSnapshotId: string | null;
  executionPlan: RunRootQuery_pipelineRunOrError_Run_executionPlan | null;
  stepKeysToExecute: string[] | null;
  repositoryOrigin: RunRootQuery_pipelineRunOrError_Run_repositoryOrigin | null;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
  stepStats: RunRootQuery_pipelineRunOrError_Run_stepStats[];
}

export type RunRootQuery_pipelineRunOrError = RunRootQuery_pipelineRunOrError_RunNotFoundError | RunRootQuery_pipelineRunOrError_Run;

export interface RunRootQuery {
  pipelineRunOrError: RunRootQuery_pipelineRunOrError;
}

export interface RunRootQueryVariables {
  runId: string;
}
