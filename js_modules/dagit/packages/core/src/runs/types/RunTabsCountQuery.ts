/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunTabsCountQuery
// ====================================================

export interface RunTabsCountQuery_queuedCount_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface RunTabsCountQuery_queuedCount_Runs {
  __typename: "Runs";
  count: number | null;
}

export type RunTabsCountQuery_queuedCount = RunTabsCountQuery_queuedCount_InvalidPipelineRunsFilterError | RunTabsCountQuery_queuedCount_Runs;

export interface RunTabsCountQuery_inProgressCount_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface RunTabsCountQuery_inProgressCount_Runs {
  __typename: "Runs";
  count: number | null;
}

export type RunTabsCountQuery_inProgressCount = RunTabsCountQuery_inProgressCount_InvalidPipelineRunsFilterError | RunTabsCountQuery_inProgressCount_Runs;

export interface RunTabsCountQuery {
  queuedCount: RunTabsCountQuery_queuedCount;
  inProgressCount: RunTabsCountQuery_inProgressCount;
}

export interface RunTabsCountQueryVariables {
  queuedFilter: RunsFilter;
  inProgressFilter: RunsFilter;
}
