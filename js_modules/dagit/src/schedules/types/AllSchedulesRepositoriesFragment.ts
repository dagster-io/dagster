// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineRunStatus, JobType, JobStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AllSchedulesRepositoriesFragment
// ====================================================

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError = AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PythonError | AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet_partitionStatusesOrError;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData = AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_SensorJobData | AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData_ScheduleJobData;

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error_cause | null;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks_error | null;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_repositoryOrigin;
  jobSpecificData: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_jobSpecificData | null;
  runs: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_runs[];
  ticks: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_futureTicks_results {
  __typename: "FutureJobTick";
  timestamp: number;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_futureTicks {
  __typename: "FutureJobTicks";
  results: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_futureTicks_results[];
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_partitionSet | null;
  scheduleState: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_scheduleState;
  futureTicks: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules_futureTicks;
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection_nodes {
  __typename: "Repository";
  id: string;
  name: string;
  location: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_location;
  schedules: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes_schedules[];
}

export interface AllSchedulesRepositoriesFragment_RepositoryConnection {
  __typename: "RepositoryConnection";
  nodes: AllSchedulesRepositoriesFragment_RepositoryConnection_nodes[];
}

export interface AllSchedulesRepositoriesFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesRepositoriesFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesRepositoriesFragment_PythonError_cause | null;
}

export type AllSchedulesRepositoriesFragment = AllSchedulesRepositoriesFragment_RepositoryConnection | AllSchedulesRepositoriesFragment_PythonError;
