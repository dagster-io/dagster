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

export interface SensorsRootQuery_sensorsOrError_Sensors_results_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin_repositoryLocationMetadata[];
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
  status: PipelineRunStatus;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error_cause | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks_error | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_repositoryOrigin;
  jobSpecificData: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_jobSpecificData | null;
  runs: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_runs[];
  ticks: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState_ticks[];
  runningCount: number;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  minIntervalSeconds: number;
  nextTick: SensorsRootQuery_sensorsOrError_Sensors_results_nextTick | null;
  sensorState: SensorsRootQuery_sensorsOrError_Sensors_results_sensorState;
}

export interface SensorsRootQuery_sensorsOrError_Sensors {
  __typename: "Sensors";
  results: SensorsRootQuery_sensorsOrError_Sensors_results[];
}

export type SensorsRootQuery_sensorsOrError = SensorsRootQuery_sensorsOrError_RepositoryNotFoundError | SensorsRootQuery_sensorsOrError_PythonError | SensorsRootQuery_sensorsOrError_Sensors;

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  ticks: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
}

export interface SensorsRootQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: SensorsRootQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface SensorsRootQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type SensorsRootQuery_unloadableJobStatesOrError = SensorsRootQuery_unloadableJobStatesOrError_JobStates | SensorsRootQuery_unloadableJobStatesOrError_PythonError;

export interface SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface SensorsRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SensorsRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface SensorsRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: SensorsRootQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface SensorsRootQuery_instance {
  __typename: "Instance";
  daemonHealth: SensorsRootQuery_instance_daemonHealth;
}

export interface SensorsRootQuery {
  sensorsOrError: SensorsRootQuery_sensorsOrError;
  unloadableJobStatesOrError: SensorsRootQuery_unloadableJobStatesOrError;
  instance: SensorsRootQuery_instance;
}

export interface SensorsRootQueryVariables {
  repositorySelector: RepositorySelector;
  jobType: JobType;
}
