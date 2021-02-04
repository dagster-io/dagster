// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobType, PipelineRunStatus, JobStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AllSchedulesQuery
// ====================================================

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError = AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError | AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData = AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData | AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData;

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause | null;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin;
  jobSpecificData: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData | null;
  runs: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureJobTicks";
  results: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  schedules: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes_schedules[];
}

export interface AllSchedulesQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: AllSchedulesQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface AllSchedulesQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesQuery_repositoriesOrError_PythonError_cause | null;
}

export type AllSchedulesQuery_repositoriesOrError = AllSchedulesQuery_repositoriesOrError_RepositoryConnection | AllSchedulesQuery_repositoriesOrError_PythonError;

export interface AllSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface AllSchedulesQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: AllSchedulesQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface AllSchedulesQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: AllSchedulesQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface AllSchedulesQuery_instance {
  __typename: "Instance";
  daemonHealth: AllSchedulesQuery_instance_daemonHealth;
}

export interface AllSchedulesQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface AllSchedulesQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface AllSchedulesQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesQuery_scheduler_PythonError_cause | null;
}

export type AllSchedulesQuery_scheduler = AllSchedulesQuery_scheduler_SchedulerNotDefinedError | AllSchedulesQuery_scheduler_Scheduler | AllSchedulesQuery_scheduler_PythonError;

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  ticks: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: AllSchedulesQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type AllSchedulesQuery_unloadableJobStatesOrError = AllSchedulesQuery_unloadableJobStatesOrError_JobStates | AllSchedulesQuery_unloadableJobStatesOrError_PythonError;

export interface AllSchedulesQuery {
  repositoriesOrError: AllSchedulesQuery_repositoriesOrError;
  instance: AllSchedulesQuery_instance;
  scheduler: AllSchedulesQuery_scheduler;
  unloadableJobStatesOrError: AllSchedulesQuery_unloadableJobStatesOrError;
}

export interface AllSchedulesQueryVariables {
  jobType?: JobType | null;
}
