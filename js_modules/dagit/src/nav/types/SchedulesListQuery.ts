// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesListQuery
// ====================================================

export interface SchedulesListQuery_schedulesOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError" | "PythonError";
}

export interface SchedulesListQuery_schedulesOrError_Schedules_results_scheduleState {
  __typename: "JobState";
  id: string;
  status: JobStatus;
}

export interface SchedulesListQuery_schedulesOrError_Schedules_results {
  __typename: "Schedule";
  id: string;
  name: string;
  scheduleState: SchedulesListQuery_schedulesOrError_Schedules_results_scheduleState | null;
}

export interface SchedulesListQuery_schedulesOrError_Schedules {
  __typename: "Schedules";
  results: SchedulesListQuery_schedulesOrError_Schedules_results[];
}

export type SchedulesListQuery_schedulesOrError = SchedulesListQuery_schedulesOrError_RepositoryNotFoundError | SchedulesListQuery_schedulesOrError_Schedules;

export interface SchedulesListQuery {
  schedulesOrError: SchedulesListQuery_schedulesOrError;
}

export interface SchedulesListQueryVariables {
  repositorySelector: RepositorySelector;
}
