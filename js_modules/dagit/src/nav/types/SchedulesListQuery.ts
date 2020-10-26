// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesListQuery
// ====================================================

export interface SchedulesListQuery_scheduleDefinitionsOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError" | "PythonError";
}

export interface SchedulesListQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState {
  __typename: "ScheduleState";
  status: ScheduleStatus;
}

export interface SchedulesListQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results {
  __typename: "ScheduleDefinition";
  name: string;
  scheduleState: SchedulesListQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results_scheduleState | null;
}

export interface SchedulesListQuery_scheduleDefinitionsOrError_ScheduleDefinitions {
  __typename: "ScheduleDefinitions";
  results: SchedulesListQuery_scheduleDefinitionsOrError_ScheduleDefinitions_results[];
}

export type SchedulesListQuery_scheduleDefinitionsOrError = SchedulesListQuery_scheduleDefinitionsOrError_RepositoryNotFoundError | SchedulesListQuery_scheduleDefinitionsOrError_ScheduleDefinitions;

export interface SchedulesListQuery {
  scheduleDefinitionsOrError: SchedulesListQuery_scheduleDefinitionsOrError;
}

export interface SchedulesListQueryVariables {
  repositorySelector: RepositorySelector;
}
