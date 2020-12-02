// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PartitionRunStatus, JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

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

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError_PythonError {
  __typename: "PythonError";
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError_Partitions_results {
  __typename: "Partition";
  name: string;
  status: PartitionRunStatus;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError_Partitions {
  __typename: "Partitions";
  results: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError_Partitions_results[];
}

export type InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError = InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError_PythonError | InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError_Partitions;

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  name: string;
  partitionsOrError: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_partitionSet_partitionsOrError;
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

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData = InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData | InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData;

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_runs {
  __typename: "PipelineRun";
  id: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runs: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_runs[];
  error: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin;
  jobSpecificData: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData | null;
  runs: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureJobTicks";
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
  scheduleState: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick {
  __typename: "FutureJobTick";
  timestamp: number;
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
  status: PipelineRunStatus;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_runs {
  __typename: "PipelineRun";
  id: string;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error_cause | null;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runs: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_runs[];
  error: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks_error | null;
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
  ticks: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_sensorState_ticks[];
  runningCount: number;
}

export interface InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  nextTick: InstanceJobsRootQuery_repositoriesOrError_RepositoryConnection_nodes_sensors_nextTick | null;
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
  status: PipelineRunStatus;
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_runs {
  __typename: "PipelineRun";
  id: string;
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error_cause | null;
}

export interface InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runs: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_runs[];
  error: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks_error | null;
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
  ticks: InstanceJobsRootQuery_unloadableJobStatesOrError_JobStates_results_ticks[];
  runningCount: number;
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
