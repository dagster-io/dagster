// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorsRootQuery
// ====================================================

export interface SensorsRootQuery_sensorsOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SensorsRootQuery_sensorsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_sensorsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_sensorsOrError_PythonError_cause | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_jobSpecificData = SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_jobSpecificData_SensorJobData | SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_jobSpecificData_ScheduleJobData;

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  jobSpecificData: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_jobSpecificData | null;
  runs: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_runs[];
  ticks: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks[];
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  sensorState: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState;
}

export interface SensorsRootQuery_sensorsOrError_Sensors {
  __typename: "Sensors";
  results: SensorsRootQuery_sensorsOrError_Sensors_results[];
}

export type SensorsRootQuery_sensorsOrError = SensorsRootQuery_sensorsOrError_RepositoryNotFoundError | SensorsRootQuery_sensorsOrError_PythonError | SensorsRootQuery_sensorsOrError_Sensors;

export interface SensorsRootQuery {
  sensorsOrError: SensorsRootQuery_sensorsOrError;
}

export interface SensorsRootQueryVariables {
  repositorySelector: RepositorySelector;
}
