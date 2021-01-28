// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunGroupPanelQuery
// ====================================================

export interface RunGroupPanelQuery_runGroupOrError_RunGroupNotFoundError {
  __typename: "RunGroupNotFoundError";
}

export interface RunGroupPanelQuery_runGroupOrError_PythonError {
  __typename: "PythonError";
  message: string;
}

export interface RunGroupPanelQuery_runGroupOrError_RunGroup_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats_PythonError_cause | null;
}

export type RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats = RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats_PipelineRunStatsSnapshot | RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats_PythonError;

export interface RunGroupPanelQuery_runGroupOrError_RunGroup_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  parentRunId: string | null;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  pipelineName: string;
  tags: RunGroupPanelQuery_runGroupOrError_RunGroup_runs_tags[];
  stats: RunGroupPanelQuery_runGroupOrError_RunGroup_runs_stats;
}

export interface RunGroupPanelQuery_runGroupOrError_RunGroup {
  __typename: "RunGroup";
  rootRunId: string;
  runs: (RunGroupPanelQuery_runGroupOrError_RunGroup_runs | null)[] | null;
}

export type RunGroupPanelQuery_runGroupOrError = RunGroupPanelQuery_runGroupOrError_RunGroupNotFoundError | RunGroupPanelQuery_runGroupOrError_PythonError | RunGroupPanelQuery_runGroupOrError_RunGroup;

export interface RunGroupPanelQuery {
  runGroupOrError: RunGroupPanelQuery_runGroupOrError;
}

export interface RunGroupPanelQueryVariables {
  runId: string;
}
