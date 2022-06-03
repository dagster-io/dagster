/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PreviousRunsForScheduleQuery
// ====================================================

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_assetSelection {
  __typename: "AssetKey";
  path: string[];
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  repositoryOrigin: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  assetSelection: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_assetSelection[] | null;
  tags: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results_tags[];
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs_results[];
}

export interface PreviousRunsForScheduleQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
  message: string;
}

export type PreviousRunsForScheduleQuery_pipelineRunsOrError = PreviousRunsForScheduleQuery_pipelineRunsOrError_Runs | PreviousRunsForScheduleQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError;

export interface PreviousRunsForScheduleQuery {
  pipelineRunsOrError: PreviousRunsForScheduleQuery_pipelineRunsOrError;
}

export interface PreviousRunsForScheduleQueryVariables {
  filter?: RunsFilter | null;
  limit?: number | null;
}
