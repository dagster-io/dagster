// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AllSensorsQuery
// ====================================================

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData = AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData | AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause | null;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error | null;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin;
  jobSpecificData: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData | null;
  runs: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs[];
  ticks: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks[];
  runningCount: number;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  minIntervalSeconds: number;
  nextTick: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick | null;
  sensorState: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState;
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  sensors: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors[];
}

export interface AllSensorsQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: AllSensorsQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface AllSensorsQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsQuery_repositoriesOrError_PythonError_cause | null;
}

export type AllSensorsQuery_repositoriesOrError = AllSensorsQuery_repositoriesOrError_RepositoryConnection | AllSensorsQuery_repositoriesOrError_PythonError;

export interface AllSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface AllSensorsQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: AllSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface AllSensorsQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: AllSensorsQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface AllSensorsQuery_instance {
  __typename: "Instance";
  daemonHealth: AllSensorsQuery_instance_daemonHealth;
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  ticks: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
}

export interface AllSensorsQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: AllSensorsQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface AllSensorsQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type AllSensorsQuery_unloadableJobStatesOrError = AllSensorsQuery_unloadableJobStatesOrError_JobStates | AllSensorsQuery_unloadableJobStatesOrError_PythonError;

export interface AllSensorsQuery {
  repositoriesOrError: AllSensorsQuery_repositoriesOrError;
  instance: AllSensorsQuery_instance;
  unloadableJobStatesOrError: AllSensorsQuery_unloadableJobStatesOrError;
}

export interface AllSensorsQueryVariables {
  jobType?: JobType | null;
}
