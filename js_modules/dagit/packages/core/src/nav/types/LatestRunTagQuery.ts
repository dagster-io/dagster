/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LatestRunTagQuery
// ====================================================

export interface LatestRunTagQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface LatestRunTagQuery_pipelineRunsOrError_Runs_results {
  __typename: "Run";
  id: string;
  status: RunStatus;
  runId: string;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface LatestRunTagQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: LatestRunTagQuery_pipelineRunsOrError_Runs_results[];
}

export type LatestRunTagQuery_pipelineRunsOrError = LatestRunTagQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | LatestRunTagQuery_pipelineRunsOrError_Runs;

export interface LatestRunTagQuery {
  pipelineRunsOrError: LatestRunTagQuery_pipelineRunsOrError;
}

export interface LatestRunTagQueryVariables {
  runsFilter?: RunsFilter | null;
}
