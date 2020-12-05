// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobTickStatus, PipelineRunStatus, ScheduleStatus, JobType, JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: InstanceJobsRootQuery
// ====================================================

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin_repositoryLocationMetadata[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData = InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: JobTickStatus;
  timestamp: number;
  tickSpecificData: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_tickSpecificData | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runsCount: number;
  runs: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "ScheduleFutureTicks";
  results: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState | null;
  futureTicks: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData = InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_SensorJobData | InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData_ScheduleJobData;

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_repositoryOrigin;
  jobSpecificData: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_jobSpecificData | null;
  runs: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_runs[];
  runsCount: number;
  ticks: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  sensorState: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  origin: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_origin;
  location: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_location;
  schedules: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules[];
  sensors: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceJobsRootQuery_repositoriesOrError_PythonError_cause | null;
}

export type InstanceJobsRootQuery_repositoriesOrError = InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection | InstanceJobsRootQuery_repositoriesOrError_PythonError;

export interface InstanceJobsRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface InstanceJobsRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface InstanceJobsRootQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceJobsRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceJobsRootQuery_scheduler_PythonError_cause | null;
}

export type InstanceJobsRootQuery_scheduler = InstanceJobsRootQuery_scheduler_SchedulerNotDefinedError | InstanceJobsRootQuery_scheduler_Scheduler | InstanceJobsRootQuery_scheduler_PythonError;

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData = InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_SensorJobData | InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData_ScheduleJobData;

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_repositoryOrigin;
  jobSpecificData: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_jobSpecificData | null;
  runs: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_runs[];
  runsCount: number;
  ticks: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates {
  __typename: "JobStates";
  results: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results[];
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceJobsRootQuery_unloadableJobStatesOrError_PythonError_cause | null;
}

export type InstanceJobsRootQuery_unloadableJobStatesOrError = InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates | InstanceJobsRootQuery_unloadableJobStatesOrError_PythonError;

export interface InstanceJobsRootQuery {
  repositoriesOrError: InstanceJobsRootQuery_repositoriesOrError;
  scheduler: InstanceJobsRootQuery_scheduler;
  unloadableJobStatesOrError: InstanceJobsRootQuery_unloadableJobStatesOrError;
}
