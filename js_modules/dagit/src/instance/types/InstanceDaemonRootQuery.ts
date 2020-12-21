// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DaemonType, PipelineRunStatus, JobType, JobStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceDaemonRootQuery
// ====================================================

export interface InstanceDaemonRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: DaemonType;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatTime: number | null;
}

export interface InstanceDaemonRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: InstanceDaemonRootQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceDaemonRootQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceDaemonRootQuery_instance_daemonHealth;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin_repositoryLocationMetadata[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError = InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError | InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  name: string;
  partitionStatusesOrError: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData = InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData | InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData;

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause | null;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin;
  jobSpecificData: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData | null;
  runs: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureJobTicks";
  results: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData = InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData | InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause | null;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error | null;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin;
  jobSpecificData: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData | null;
  runs: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs[];
  ticks: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks[];
  runningCount: number;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  nextTick: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick | null;
  sensorState: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState;
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  origin: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin;
  location: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  schedules: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules[];
  sensors: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceDaemonRootQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceDaemonRootQuery_repositoriesOrError_PythonError_cause | null;
}

export type InstanceDaemonRootQuery_repositoriesOrError = InstanceDaemonRootQuery_repositoriesOrError_RepositoryConnection | InstanceDaemonRootQuery_repositoriesOrError_PythonError;

export interface InstanceDaemonRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface InstanceDaemonRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface InstanceDaemonRootQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceDaemonRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceDaemonRootQuery_scheduler_PythonError_cause | null;
}

export type InstanceDaemonRootQuery_scheduler = InstanceDaemonRootQuery_scheduler_SchedulerNotDefinedError | InstanceDaemonRootQuery_scheduler_Scheduler | InstanceDaemonRootQuery_scheduler_PythonError;

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  ticks: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceDaemonRootQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceDaemonRootQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type InstanceDaemonRootQuery_unloadableJobStatesOrError = InstanceDaemonRootQuery_unloadableJobStatesOrError_JobStates | InstanceDaemonRootQuery_unloadableJobStatesOrError_PythonError;

export interface InstanceDaemonRootQuery {
  instance: InstanceDaemonRootQuery_instance;
  repositoriesOrError: InstanceDaemonRootQuery_repositoriesOrError;
  scheduler: InstanceDaemonRootQuery_scheduler;
  unloadableJobStatesOrError: InstanceDaemonRootQuery_unloadableJobStatesOrError;
}
