// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RepositorySensorsFragment
// ====================================================

export interface RepositorySensorsFragment_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositorySensorsFragment_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: RepositorySensorsFragment_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface RepositorySensorsFragment_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface RepositorySensorsFragment_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type RepositorySensorsFragment_sensors_sensorState_jobSpecificData = RepositorySensorsFragment_sensors_sensorState_jobSpecificData_SensorJobData | RepositorySensorsFragment_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface RepositorySensorsFragment_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface RepositorySensorsFragment_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface RepositorySensorsFragment_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: RepositorySensorsFragment_sensors_sensorState_repositoryOrigin;
  jobSpecificData: RepositorySensorsFragment_sensors_sensorState_jobSpecificData | null;
  runs: RepositorySensorsFragment_sensors_sensorState_runs[];
  runsCount: number;
  ticks: RepositorySensorsFragment_sensors_sensorState_ticks[];
}

export interface RepositorySensorsFragment_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  sensorState: RepositorySensorsFragment_sensors_sensorState;
}

export interface RepositorySensorsFragment_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RepositorySensorsFragment_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: RepositorySensorsFragment_origin_repositoryLocationMetadata[];
}

export interface RepositorySensorsFragment_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RepositorySensorsFragment {
  __typename: "Repository";
  name: string;
  id: string;
  sensors: RepositorySensorsFragment_sensors[];
  origin: RepositorySensorsFragment_origin;
  location: RepositorySensorsFragment_location;
}
