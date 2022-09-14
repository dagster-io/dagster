/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunsFilter, RunStatus, RepositoryLocationLoadStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunTimelineQuery
// ====================================================

export interface RunTimelineQuery_unterminated_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface RunTimelineQuery_unterminated_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunTimelineQuery_unterminated_Runs_results {
  __typename: "Run";
  id: string;
  pipelineName: string;
  repositoryOrigin: RunTimelineQuery_unterminated_Runs_results_repositoryOrigin | null;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface RunTimelineQuery_unterminated_Runs {
  __typename: "Runs";
  results: RunTimelineQuery_unterminated_Runs_results[];
}

export type RunTimelineQuery_unterminated = RunTimelineQuery_unterminated_InvalidPipelineRunsFilterError | RunTimelineQuery_unterminated_Runs;

export interface RunTimelineQuery_terminated_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface RunTimelineQuery_terminated_Runs_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface RunTimelineQuery_terminated_Runs_results {
  __typename: "Run";
  id: string;
  pipelineName: string;
  repositoryOrigin: RunTimelineQuery_terminated_Runs_results_repositoryOrigin | null;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface RunTimelineQuery_terminated_Runs {
  __typename: "Runs";
  results: RunTimelineQuery_terminated_Runs_results[];
}

export type RunTimelineQuery_terminated = RunTimelineQuery_terminated_InvalidPipelineRunsFilterError | RunTimelineQuery_terminated_Runs;

export interface RunTimelineQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks_results[];
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  pipelineName: string;
  scheduleState: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState;
  executionTimezone: string | null;
  futureTicks: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_futureTicks;
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  schedules: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
}

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
  repositories: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export type RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError | RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation;

export interface RunTimelineQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_displayMetadata[];
  locationOrLoadError: RunTimelineQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface RunTimelineQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: RunTimelineQuery_workspaceOrError_Workspace_locationEntries[];
}

export type RunTimelineQuery_workspaceOrError = RunTimelineQuery_workspaceOrError_PythonError | RunTimelineQuery_workspaceOrError_Workspace;

export interface RunTimelineQuery {
  unterminated: RunTimelineQuery_unterminated;
  terminated: RunTimelineQuery_terminated;
  workspaceOrError: RunTimelineQuery_workspaceOrError;
}

export interface RunTimelineQueryVariables {
  inProgressFilter: RunsFilter;
  terminatedFilter: RunsFilter;
}
