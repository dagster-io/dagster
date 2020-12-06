// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_partitionSet {
  __typename: "PartitionSet";
  name: string;
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

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
  tags: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_runs_tags[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_runs {
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
  runs: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks_runs[];
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
  runsCount: number;
  ticks: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_schedules_futureTicks {
  __typename: "ScheduleFutureTicks";
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
  scheduleState: SchedulesRootQuery_repositoryOrError_Repository_schedules_scheduleState | null;
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

export interface SchedulesRootQuery_repositoryOrError_Repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  schedules: SchedulesRootQuery_repositoryOrError_Repository_schedules[];
  origin: SchedulesRootQuery_repositoryOrError_Repository_origin;
  location: SchedulesRootQuery_repositoryOrError_Repository_location;
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

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
  tags: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_runs_tags[];
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_runs {
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
  runs: SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_runs[];
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
  runsCount: number;
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

export interface SchedulesRootQuery {
  repositoryOrError: SchedulesRootQuery_repositoryOrError;
  scheduler: SchedulesRootQuery_scheduler;
  unloadableJobStatesOrError: SchedulesRootQuery_unloadableJobStatesOrError;
}

export interface SchedulesRootQueryVariables {
  repositorySelector: RepositorySelector;
  jobType: JobType;
}
