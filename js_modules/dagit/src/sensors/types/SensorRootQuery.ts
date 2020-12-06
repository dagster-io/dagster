// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorRootQuery
// ====================================================

export interface SensorRootQuery_sensorOrError_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "PythonError";
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type SensorRootQuery_sensorOrError_Sensor_sensorState_jobSpecificData = SensorRootQuery_sensorOrError_Sensor_sensorState_jobSpecificData_SensorJobData | SensorRootQuery_sensorOrError_Sensor_sensorState_jobSpecificData_ScheduleJobData;

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
  tags: SensorRootQuery_sensorOrError_Sensor_sensorState_runs_tags[];
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error_cause | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  runs: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_runs[];
  error: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks_error | null;
}

export interface SensorRootQuery_sensorOrError_Sensor_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: SensorRootQuery_sensorOrError_Sensor_sensorState_repositoryOrigin;
  jobSpecificData: SensorRootQuery_sensorOrError_Sensor_sensorState_jobSpecificData | null;
  runs: SensorRootQuery_sensorOrError_Sensor_sensorState_runs[];
  runsCount: number;
  ticks: SensorRootQuery_sensorOrError_Sensor_sensorState_ticks[];
  runningCount: number;
}

export interface SensorRootQuery_sensorOrError_Sensor {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  sensorState: SensorRootQuery_sensorOrError_Sensor_sensorState;
}

export type SensorRootQuery_sensorOrError = SensorRootQuery_sensorOrError_SensorNotFoundError | SensorRootQuery_sensorOrError_Sensor;

export interface SensorRootQuery {
  sensorOrError: SensorRootQuery_sensorOrError;
}

export interface SensorRootQueryVariables {
  sensorSelector: SensorSelector;
}
