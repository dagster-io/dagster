// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstigationListQuery
// ====================================================

export interface InstigationListQuery_schedulesOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError" | "PythonError";
}

export interface InstigationListQuery_schedulesOrError_Schedules_results_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface InstigationListQuery_schedulesOrError_Schedules_results_scheduleState {
  __typename: "InstigationState";
  id: string;
  repositoryOrigin: InstigationListQuery_schedulesOrError_Schedules_results_scheduleState_repositoryOrigin;
  status: InstigationStatus;
}

export interface InstigationListQuery_schedulesOrError_Schedules_results {
  __typename: "Schedule";
  id: string;
  name: string;
  scheduleState: InstigationListQuery_schedulesOrError_Schedules_results_scheduleState;
}

export interface InstigationListQuery_schedulesOrError_Schedules {
  __typename: "Schedules";
  results: InstigationListQuery_schedulesOrError_Schedules_results[];
}

export type InstigationListQuery_schedulesOrError = InstigationListQuery_schedulesOrError_RepositoryNotFoundError | InstigationListQuery_schedulesOrError_Schedules;

export interface InstigationListQuery_sensorsOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError" | "PythonError";
}

export interface InstigationListQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface InstigationListQuery_sensorsOrError_Sensors_results_sensorState {
  __typename: "InstigationState";
  id: string;
  repositoryOrigin: InstigationListQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin;
  status: InstigationStatus;
}

export interface InstigationListQuery_sensorsOrError_Sensors_results {
  __typename: "Sensor";
  id: string;
  name: string;
  sensorState: InstigationListQuery_sensorsOrError_Sensors_results_sensorState;
}

export interface InstigationListQuery_sensorsOrError_Sensors {
  __typename: "Sensors";
  results: InstigationListQuery_sensorsOrError_Sensors_results[];
}

export type InstigationListQuery_sensorsOrError = InstigationListQuery_sensorsOrError_RepositoryNotFoundError | InstigationListQuery_sensorsOrError_Sensors;

export interface InstigationListQuery {
  schedulesOrError: InstigationListQuery_schedulesOrError;
  sensorsOrError: InstigationListQuery_sensorsOrError;
}

export interface InstigationListQueryVariables {
  repositorySelector: RepositorySelector;
}
