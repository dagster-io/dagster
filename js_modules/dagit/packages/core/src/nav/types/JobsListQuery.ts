// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: JobsListQuery
// ====================================================

export interface JobsListQuery_schedulesOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError" | "PythonError";
}

export interface JobsListQuery_schedulesOrError_Schedules_results_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface JobsListQuery_schedulesOrError_Schedules_results_scheduleState {
  __typename: "InstigationState";
  id: string;
  repositoryOrigin: JobsListQuery_schedulesOrError_Schedules_results_scheduleState_repositoryOrigin;
  status: InstigationStatus;
}

export interface JobsListQuery_schedulesOrError_Schedules_results {
  __typename: "Schedule";
  id: string;
  name: string;
  scheduleState: JobsListQuery_schedulesOrError_Schedules_results_scheduleState;
}

export interface JobsListQuery_schedulesOrError_Schedules {
  __typename: "Schedules";
  results: JobsListQuery_schedulesOrError_Schedules_results[];
}

export type JobsListQuery_schedulesOrError = JobsListQuery_schedulesOrError_RepositoryNotFoundError | JobsListQuery_schedulesOrError_Schedules;

export interface JobsListQuery_sensorsOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError" | "PythonError";
}

export interface JobsListQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface JobsListQuery_sensorsOrError_Sensors_results_sensorState {
  __typename: "InstigationState";
  id: string;
  repositoryOrigin: JobsListQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin;
  status: InstigationStatus;
}

export interface JobsListQuery_sensorsOrError_Sensors_results {
  __typename: "Sensor";
  id: string;
  name: string;
  sensorState: JobsListQuery_sensorsOrError_Sensors_results_sensorState;
}

export interface JobsListQuery_sensorsOrError_Sensors {
  __typename: "Sensors";
  results: JobsListQuery_sensorsOrError_Sensors_results[];
}

export type JobsListQuery_sensorsOrError = JobsListQuery_sensorsOrError_RepositoryNotFoundError | JobsListQuery_sensorsOrError_Sensors;

export interface JobsListQuery {
  schedulesOrError: JobsListQuery_schedulesOrError;
  sensorsOrError: JobsListQuery_sensorsOrError;
}

export interface JobsListQueryVariables {
  repositorySelector: RepositorySelector;
}
