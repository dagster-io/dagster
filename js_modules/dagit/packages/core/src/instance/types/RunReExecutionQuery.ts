/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepKind, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunReExecutionQuery
// ====================================================

export interface RunReExecutionQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunReExecutionQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn[];
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: RunReExecutionQuery_pipelineRunOrError_Run_executionPlan_steps_inputs[];
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_executionPlan {
  __typename: "ExecutionPlan";
  artifactsPersisted: boolean;
  steps: RunReExecutionQuery_pipelineRunOrError_Run_executionPlan_steps[];
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_stepStats_attempts {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_stepStats_markers {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunReExecutionQuery_pipelineRunOrError_Run_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  status: StepEventStatus | null;
  startTime: number | null;
  endTime: number | null;
  attempts: RunReExecutionQuery_pipelineRunOrError_Run_stepStats_attempts[];
  markers: RunReExecutionQuery_pipelineRunOrError_Run_stepStats_markers[];
}

export interface RunReExecutionQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  runConfig: any;
  runId: string;
  canTerminate: boolean;
  status: RunStatus;
  mode: string;
  tags: RunReExecutionQuery_pipelineRunOrError_Run_tags[];
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  pipelineSnapshotId: string | null;
  executionPlan: RunReExecutionQuery_pipelineRunOrError_Run_executionPlan | null;
  stepKeysToExecute: string[] | null;
  repositoryOrigin: RunReExecutionQuery_pipelineRunOrError_Run_repositoryOrigin | null;
  startTime: number | null;
  endTime: number | null;
  stepStats: RunReExecutionQuery_pipelineRunOrError_Run_stepStats[];
}

export type RunReExecutionQuery_pipelineRunOrError = RunReExecutionQuery_pipelineRunOrError_RunNotFoundError | RunReExecutionQuery_pipelineRunOrError_Run;

export interface RunReExecutionQuery {
  pipelineRunOrError: RunReExecutionQuery_pipelineRunOrError;
}

export interface RunReExecutionQueryVariables {
  runId: string;
}
