// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunDetailsTestQuery
// ====================================================

export interface RunDetailsTestQuery_pipelineRunOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface RunDetailsTestQuery_pipelineRunOrError_PipelineRun_stats_PythonError {
  __typename: "PythonError";
}

export interface RunDetailsTestQuery_pipelineRunOrError_PipelineRun_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  endTime: number | null;
  startTime: number | null;
}

export type RunDetailsTestQuery_pipelineRunOrError_PipelineRun_stats = RunDetailsTestQuery_pipelineRunOrError_PipelineRun_stats_PythonError | RunDetailsTestQuery_pipelineRunOrError_PipelineRun_stats_PipelineRunStatsSnapshot;

export interface RunDetailsTestQuery_pipelineRunOrError_PipelineRun {
  __typename: "PipelineRun";
  id: string;
  stats: RunDetailsTestQuery_pipelineRunOrError_PipelineRun_stats;
  status: PipelineRunStatus;
}

export type RunDetailsTestQuery_pipelineRunOrError = RunDetailsTestQuery_pipelineRunOrError_PipelineRunNotFoundError | RunDetailsTestQuery_pipelineRunOrError_PipelineRun;

export interface RunDetailsTestQuery {
  pipelineRunOrError: RunDetailsTestQuery_pipelineRunOrError;
}
