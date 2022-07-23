/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunGroupPanelQuery
// ====================================================

export interface RunGroupPanelQuery_runGroupOrError_RunGroupNotFoundError {
  __typename: "RunGroupNotFoundError";
}

export interface RunGroupPanelQuery_runGroupOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunGroupPanelQuery_runGroupOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: RunGroupPanelQuery_runGroupOrError_PythonError_causes[];
}

export interface RunGroupPanelQuery_runGroupOrError_RunGroup_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RunGroupPanelQuery_runGroupOrError_RunGroup_runs {
  __typename: "Run";
  id: string;
  runId: string;
  parentRunId: string | null;
  status: RunStatus;
  stepKeysToExecute: string[] | null;
  pipelineName: string;
  tags: RunGroupPanelQuery_runGroupOrError_RunGroup_runs_tags[];
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
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
