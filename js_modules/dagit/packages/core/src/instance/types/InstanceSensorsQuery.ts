// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus, JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceSensorsQuery
// ====================================================

export interface InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceSensorsQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: InstanceSensorsQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceSensorsQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceSensorsQuery_instance_daemonHealth;
}

export interface InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
}

export interface InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
}

export type InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_displayMetadata[];
  updatedTimestamp: number;
  locationOrLoadError: InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface InstanceSensorsQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: InstanceSensorsQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface InstanceSensorsQuery_workspaceOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_workspaceOrError_PythonError_cause | null;
}

export type InstanceSensorsQuery_workspaceOrError = InstanceSensorsQuery_workspaceOrError_Workspace | InstanceSensorsQuery_workspaceOrError_PythonError;

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData = InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData | InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error | null;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin;
  jobSpecificData: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData | null;
  runs: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs[];
  ticks: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks[];
  runningCount: number;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  description: string | null;
  minIntervalSeconds: number;
  nextTick: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick | null;
  sensorState: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState;
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  displayMetadata: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata[];
  sensors: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes_sensors[];
}

export interface InstanceSensorsQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: InstanceSensorsQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface InstanceSensorsQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_repositoriesOrError_PythonError_cause | null;
}

export type InstanceSensorsQuery_repositoriesOrError = InstanceSensorsQuery_repositoriesOrError_RepositoryConnection | InstanceSensorsQuery_repositoriesOrError_PythonError;

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  ticks: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: InstanceSensorsQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSensorsQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSensorsQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type InstanceSensorsQuery_unloadableJobStatesOrError = InstanceSensorsQuery_unloadableJobStatesOrError_JobStates | InstanceSensorsQuery_unloadableJobStatesOrError_PythonError;

export interface InstanceSensorsQuery {
  instance: InstanceSensorsQuery_instance;
  workspaceOrError: InstanceSensorsQuery_workspaceOrError;
  repositoriesOrError: InstanceSensorsQuery_repositoriesOrError;
  unloadableJobStatesOrError: InstanceSensorsQuery_unloadableJobStatesOrError;
}
