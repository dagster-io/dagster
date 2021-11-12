// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PreviousRunsFragment
// ====================================================

export interface PreviousRunsFragment_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface PreviousRunsFragment_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PreviousRunsFragment_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PreviousRunsFragment_Runs_results_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PreviousRunsFragment_Runs_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PreviousRunsFragment_Runs_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PreviousRunsFragment_Runs_results_stats_PythonError_cause | null;
}

export type PreviousRunsFragment_Runs_results_stats = PreviousRunsFragment_Runs_results_stats_RunStatsSnapshot | PreviousRunsFragment_Runs_results_stats_PythonError;

export interface PreviousRunsFragment_Runs_results {
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
  repositoryOrigin: PreviousRunsFragment_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  tags: PreviousRunsFragment_Runs_results_tags[];
  stats: PreviousRunsFragment_Runs_results_stats;
}

export interface PreviousRunsFragment_Runs {
  __typename: "Runs";
  results: PreviousRunsFragment_Runs_results[];
}

export type PreviousRunsFragment = PreviousRunsFragment_InvalidPipelineRunsFilterError | PreviousRunsFragment_Runs;
