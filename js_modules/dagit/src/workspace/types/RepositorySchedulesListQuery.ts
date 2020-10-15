// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { RepositorySelector, ScheduleStatus, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RepositorySchedulesListQuery
// ====================================================

export interface RepositorySchedulesListQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
}

export interface RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
}

export interface RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines_schedules_scheduleState {
  __typename: "ScheduleState";
  status: ScheduleStatus;
  runs: RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines_schedules_scheduleState_runs[];
}

export interface RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines_schedules {
  __typename: "ScheduleDefinition";
  cronSchedule: string;
  mode: string;
  name: string;
  pipelineName: string;
  scheduleState: RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines_schedules_scheduleState | null;
}

export interface RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  name: string;
  schedules: RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines_schedules[];
}

export interface RepositorySchedulesListQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  pipelines: RepositorySchedulesListQuery_repositoryOrError_Repository_pipelines[];
}

export interface RepositorySchedulesListQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
  message: string;
}

export type RepositorySchedulesListQuery_repositoryOrError = RepositorySchedulesListQuery_repositoryOrError_PythonError | RepositorySchedulesListQuery_repositoryOrError_Repository | RepositorySchedulesListQuery_repositoryOrError_RepositoryNotFoundError;

export interface RepositorySchedulesListQuery {
  repositoryOrError: RepositorySchedulesListQuery_repositoryOrError;
}

export interface RepositorySchedulesListQueryVariables {
  repositorySelector: RepositorySelector;
}
