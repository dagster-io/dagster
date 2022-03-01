/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepKind, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunActionButtonsTestQuery
// ====================================================

export interface RunActionButtonsTestQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan_steps_inputs {
  __typename: "ExecutionStepInput";
  dependsOn: RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan_steps_inputs_dependsOn[];
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan_steps {
  __typename: "ExecutionStep";
  key: string;
  kind: StepKind;
  inputs: RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan_steps_inputs[];
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan {
  __typename: "ExecutionPlan";
  artifactsPersisted: boolean;
  steps: RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan_steps[];
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_stepStats_attempts {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_stepStats_markers {
  __typename: "RunMarker";
  startTime: number | null;
  endTime: number | null;
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  status: StepEventStatus | null;
  startTime: number | null;
  endTime: number | null;
  attempts: RunActionButtonsTestQuery_pipelineRunOrError_Run_stepStats_attempts[];
  markers: RunActionButtonsTestQuery_pipelineRunOrError_Run_stepStats_markers[];
}

export interface RunActionButtonsTestQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  runConfig: any;
  runId: string;
  canTerminate: boolean;
  status: RunStatus;
  mode: string;
  tags: RunActionButtonsTestQuery_pipelineRunOrError_Run_tags[];
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  pipelineSnapshotId: string | null;
  executionPlan: RunActionButtonsTestQuery_pipelineRunOrError_Run_executionPlan | null;
  stepKeysToExecute: string[] | null;
  repositoryOrigin: RunActionButtonsTestQuery_pipelineRunOrError_Run_repositoryOrigin | null;
  startTime: number | null;
  endTime: number | null;
  stepStats: RunActionButtonsTestQuery_pipelineRunOrError_Run_stepStats[];
}

export type RunActionButtonsTestQuery_pipelineRunOrError = RunActionButtonsTestQuery_pipelineRunOrError_RunNotFoundError | RunActionButtonsTestQuery_pipelineRunOrError_Run;

export interface RunActionButtonsTestQuery {
  pipelineRunOrError: RunActionButtonsTestQuery_pipelineRunOrError;
}
