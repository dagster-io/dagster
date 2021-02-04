// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AllSensorsRepositoriesFragment
// ====================================================

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData = AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData | AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause | null;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_ticks_error | null;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin;
  jobSpecificData: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData | null;
  runs: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_runs[];
  ticks: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState_ticks[];
  runningCount: number;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  minIntervalSeconds: number;
  nextTick: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_nextTick | null;
  sensorState: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors_sensorState;
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_location;
  sensors: AllSensorsRepositoriesFragment_RepositoryConnection_nodes_sensors[];
}

export interface AllSensorsRepositoriesFragment_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: AllSensorsRepositoriesFragment_RepositoryConnection_nodes[];
}

export interface AllSensorsRepositoriesFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsRepositoriesFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsRepositoriesFragment_PythonError_cause | null;
}

export type AllSensorsRepositoriesFragment = AllSensorsRepositoriesFragment_RepositoryConnection | AllSensorsRepositoriesFragment_PythonError;
