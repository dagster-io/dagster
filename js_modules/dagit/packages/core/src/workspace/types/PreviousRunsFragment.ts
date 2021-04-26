// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PreviousRunsFragment
// ====================================================

export interface PreviousRunsFragment_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface PreviousRunsFragment_PipelineRuns_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PreviousRunsFragment_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface PreviousRunsFragment_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface PreviousRunsFragment_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: PreviousRunsFragment_PipelineRuns_results_stats_PythonError_cause | null;
}

export type PreviousRunsFragment_PipelineRuns_results_stats = PreviousRunsFragment_PipelineRuns_results_stats_PipelineRunStatsSnapshot | PreviousRunsFragment_PipelineRuns_results_stats_PythonError;

export interface PreviousRunsFragment_PipelineRuns_results {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  tags: PreviousRunsFragment_PipelineRuns_results_tags[];
  stats: PreviousRunsFragment_PipelineRuns_results_stats;
}

export interface PreviousRunsFragment_PipelineRuns {
  __typename: "PipelineRuns";
  results: PreviousRunsFragment_PipelineRuns_results[];
}

export type PreviousRunsFragment = PreviousRunsFragment_InvalidPipelineRunsFilterError | PreviousRunsFragment_PipelineRuns;
