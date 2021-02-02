// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, JobType, PipelineRunStatus, JobStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulesRootQuery_repositoryOrError_Repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError = SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError_PythonError | SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet_partitionStatusesOrError;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_jobSpecificData = SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_jobSpecificData_SensorJobData | SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_jobSpecificData_ScheduleJobData;

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error_cause | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_error | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_repositoryOrigin;
  jobSpecificData: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_jobSpecificData | null;
  runs: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_runs[];
  ticks: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks {
  __typename: "FutureJobTicks";
  results: SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks_results[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet | null;
  scheduleState: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState;
  futureTicks: SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulesRootQuery_repositoryOrError_Repository_origin_repositoryLocationMetadata[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: SchedulesRootQuery_repositoryOrError_Repository_location;
  schedules: SchedulesRootQuery_repositoryOrError_Repository_schedules[];
  origin: SchedulesRootQuery_repositoryOrError_Repository_origin;
}

export interface SchedulesRootQuery_repositoryOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_repositoryOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_repositoryOrError_PythonError_cause | null;
}

export type SchedulesRootQuery_repositoryOrError = SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError | SchedulesRootQuery_repositoryOrError_Repository | SchedulesRootQuery_repositoryOrError_PythonError;

export interface SchedulesRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface SchedulesRootQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_scheduler_PythonError_cause | null;
}

export type SchedulesRootQuery_scheduler = SchedulesRootQuery_scheduler_SchedulerNotDefinedError | SchedulesRootQuery_scheduler_Scheduler | SchedulesRootQuery_scheduler_PythonError;

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  ticks: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type SchedulesRootQuery_unloadableJobStatesOrError = SchedulesRootQuery_unloadableJobStatesOrError_JobStates | SchedulesRootQuery_unloadableJobStatesOrError_PythonError;

export interface SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface SchedulesRootQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: SchedulesRootQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface SchedulesRootQuery_instance {
  __typename: "Instance";
  daemonHealth: SchedulesRootQuery_instance_daemonHealth;
}

export interface SchedulesRootQuery {
  repositoryOrError: SchedulesRootQuery_repositoryOrError;
  scheduler: SchedulesRootQuery_scheduler;
  unloadableJobStatesOrError: SchedulesRootQuery_unloadableJobStatesOrError;
  instance: SchedulesRootQuery_instance;
}

export interface SchedulesRootQueryVariables {
  repositorySelector: RepositorySelector;
  jobType: JobType;
}
