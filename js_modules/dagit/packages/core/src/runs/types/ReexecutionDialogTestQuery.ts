/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ReexecutionDialogTestQuery
// ====================================================

export interface ReexecutionDialogTestQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface ReexecutionDialogTestQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface ReexecutionDialogTestQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ReexecutionDialogTestQuery_pipelineRunsOrError_Runs_results {
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
  repositoryOrigin: ReexecutionDialogTestQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  tags: ReexecutionDialogTestQuery_pipelineRunsOrError_Runs_results_tags[];
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface ReexecutionDialogTestQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: ReexecutionDialogTestQuery_pipelineRunsOrError_Runs_results[];
}

export type ReexecutionDialogTestQuery_pipelineRunsOrError = ReexecutionDialogTestQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | ReexecutionDialogTestQuery_pipelineRunsOrError_Runs;

export interface ReexecutionDialogTestQuery {
  pipelineRunsOrError: ReexecutionDialogTestQuery_pipelineRunsOrError;
}
