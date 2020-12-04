// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, JobType, JobTickStatus, PipelineRunStatus, ScheduleStatus, JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_repositoryOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData = SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: JobTickStatus;
  timestamp: number;
  tickSpecificData: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks_tickSpecificData | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_ticks[];
  runsCount: number;
  runs: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_futureTicks {
  __typename: "ScheduleFutureTicks";
  results: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_futureTicks_results[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions {
  __typename: "ScheduleDefinition";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_partitionSet | null;
  scheduleState: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_scheduleState | null;
  futureTicks: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions_futureTicks;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_jobSpecificData = SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_jobSpecificData_SensorJobData | SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_repositoryOrigin;
  jobSpecificData: SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_jobSpecificData | null;
  runs: SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_runs[];
  runsCount: number;
  ticks: SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState_ticks[];
}

export interface SchedulesRootQuery_repositoryOrError_Repository_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  sensorState: SchedulesRootQuery_repositoryOrError_Repository_sensors_sensorState;
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
  scheduleDefinitions: SchedulesRootQuery_repositoryOrError_Repository_scheduleDefinitions[];
  sensors: SchedulesRootQuery_repositoryOrError_Repository_sensors[];
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

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SchedulesRootQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
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
