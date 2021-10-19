// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunTableRunFragment
// ====================================================

export interface RunTableRunFragment_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface RunTableRunFragment_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunTableRunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunTableRunFragment_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface RunTableRunFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunTableRunFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunTableRunFragment_stats_PythonError_cause | null;
}

export type RunTableRunFragment_stats = RunTableRunFragment_stats_RunStatsSnapshot | RunTableRunFragment_stats_PythonError;

export interface RunTableRunFragment {
  __typename: "Run";
  id: string;
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipeline: RunTableRunFragment_pipeline;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  repositoryOrigin: RunTableRunFragment_repositoryOrigin | null;
  solidSelection: string[] | null;
  tags: RunTableRunFragment_tags[];
  stats: RunTableRunFragment_stats;
}
