// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunTableRunFragment
// ====================================================

export interface RunTableRunFragment_pipeline_UnknownPipeline {
  __typename: "UnknownPipeline";
  name: string;
  solidSelection: string[] | null;
}

export interface RunTableRunFragment_pipeline_PipelineSnapshot {
  __typename: "PipelineSnapshot";
  name: string;
  solidSelection: string[] | null;
  pipelineSnapshotId: string;
}

export type RunTableRunFragment_pipeline = RunTableRunFragment_pipeline_UnknownPipeline | RunTableRunFragment_pipeline_PipelineSnapshot;

export interface RunTableRunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunTableRunFragment_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
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

export type RunTableRunFragment_stats = RunTableRunFragment_stats_PipelineRunStatsSnapshot | RunTableRunFragment_stats_PythonError;

export interface RunTableRunFragment {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipeline: RunTableRunFragment_pipeline;
  tags: RunTableRunFragment_tags[];
  stats: RunTableRunFragment_stats;
}
