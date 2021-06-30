// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, JobType, JobStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceSchedulesQuery
// ====================================================

export interface InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceSchedulesQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: InstanceSchedulesQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceSchedulesQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceSchedulesQuery_instance_daemonHealth;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError = InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError | InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData = InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData | InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData;

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause | null;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin;
  jobSpecificData: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData | null;
  runs: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureJobTicks";
  results: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  description: string | null;
  partitionSet: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  displayMetadata: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_displayMetadata[];
  schedules: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSchedulesQuery_repositoriesOrError_PythonError_cause | null;
}

export type InstanceSchedulesQuery_repositoriesOrError = InstanceSchedulesQuery_repositoriesOrError_RepositoryConnection | InstanceSchedulesQuery_repositoriesOrError_PythonError;

export interface InstanceSchedulesQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface InstanceSchedulesQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface InstanceSchedulesQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSchedulesQuery_scheduler_PythonError_cause | null;
}

export type InstanceSchedulesQuery_scheduler = InstanceSchedulesQuery_scheduler_SchedulerNotDefinedError | InstanceSchedulesQuery_scheduler_Scheduler | InstanceSchedulesQuery_scheduler_PythonError;

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  ticks: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceSchedulesQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceSchedulesQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type InstanceSchedulesQuery_unloadableJobStatesOrError = InstanceSchedulesQuery_unloadableJobStatesOrError_JobStates | InstanceSchedulesQuery_unloadableJobStatesOrError_PythonError;

export interface InstanceSchedulesQuery {
  instance: InstanceSchedulesQuery_instance;
  repositoriesOrError: InstanceSchedulesQuery_repositoriesOrError;
  scheduler: InstanceSchedulesQuery_scheduler;
  unloadableJobStatesOrError: InstanceSchedulesQuery_unloadableJobStatesOrError;
}
