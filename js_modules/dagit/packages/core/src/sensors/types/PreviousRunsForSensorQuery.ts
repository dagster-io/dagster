/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PreviousRunsForSensorQuery
// ====================================================

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results_assetSelection {
  __typename: "AssetKey";
  path: string[];
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results {
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
  repositoryOrigin: PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results_repositoryOrigin | null;
  solidSelection: string[] | null;
  assetSelection: PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results_assetSelection[] | null;
  tags: PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results_tags[];
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface PreviousRunsForSensorQuery_pipelineRunsOrError_Runs {
  __typename: "Runs";
  results: PreviousRunsForSensorQuery_pipelineRunsOrError_Runs_results[];
}

export type PreviousRunsForSensorQuery_pipelineRunsOrError = PreviousRunsForSensorQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | PreviousRunsForSensorQuery_pipelineRunsOrError_Runs;

export interface PreviousRunsForSensorQuery {
  pipelineRunsOrError: PreviousRunsForSensorQuery_pipelineRunsOrError;
}

export interface PreviousRunsForSensorQueryVariables {
  filter?: RunsFilter | null;
  limit?: number | null;
}
