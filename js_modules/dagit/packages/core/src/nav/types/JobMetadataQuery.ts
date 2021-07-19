// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, PipelineRunsFilter, PipelineRunStatus, InstigationType, InstigationStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: JobMetadataQuery
// ====================================================

export interface JobMetadataQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError_PythonError {
  __typename: "PythonError";
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runStatus: PipelineRunStatus | null;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses {
  __typename: "PartitionStatuses";
  results: JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses_results[];
}

export type JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError = JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError_PythonError | JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError_PartitionStatuses;

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  partitionStatusesOrError: JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet_partitionStatusesOrError;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_typeSpecificData = JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_typeSpecificData_SensorData | JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_typeSpecificData_ScheduleData;

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_ticks_error_cause | null;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_ticks_error | null;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryOrigin: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_repositoryOrigin;
  typeSpecificData: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_typeSpecificData | null;
  runs: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_runs[];
  ticks: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState_ticks[];
  runningCount: number;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules_futureTicks {
  __typename: "FutureInstigationTicks";
  results: JobMetadataQuery_pipelineOrError_Pipeline_schedules_futureTicks_results[];
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  description: string | null;
  partitionSet: JobMetadataQuery_pipelineOrError_Pipeline_schedules_partitionSet | null;
  scheduleState: JobMetadataQuery_pipelineOrError_Pipeline_schedules_scheduleState;
  futureTicks: JobMetadataQuery_pipelineOrError_Pipeline_schedules_futureTicks;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_nextTick {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_typeSpecificData = JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_typeSpecificData_SensorData | JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_typeSpecificData_ScheduleData;

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_ticks_error_cause | null;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_ticks {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_ticks_error | null;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryOrigin: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_repositoryOrigin;
  typeSpecificData: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_typeSpecificData | null;
  runs: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_runs[];
  ticks: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState_ticks[];
  runningCount: number;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  pipelineName: string | null;
  solidSelection: (string | null)[] | null;
  mode: string | null;
  description: string | null;
  minIntervalSeconds: number;
  nextTick: JobMetadataQuery_pipelineOrError_Pipeline_sensors_nextTick | null;
  sensorState: JobMetadataQuery_pipelineOrError_Pipeline_sensors_sensorState;
}

export interface JobMetadataQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  schedules: JobMetadataQuery_pipelineOrError_Pipeline_schedules[];
  sensors: JobMetadataQuery_pipelineOrError_Pipeline_sensors[];
}

export type JobMetadataQuery_pipelineOrError = JobMetadataQuery_pipelineOrError_PipelineNotFoundError | JobMetadataQuery_pipelineOrError_Pipeline;

export interface JobMetadataQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError {
  __typename: "InvalidPipelineRunsFilterError" | "PythonError";
}

export interface JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_assets_key {
  __typename: "AssetKey";
  path: string[];
}

export interface JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_assets {
  __typename: "Asset";
  id: string;
  key: JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_assets_key;
}

export interface JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError_cause | null;
}

export type JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats = JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats_PipelineRunStatsSnapshot | JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats_PythonError;

export interface JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results {
  __typename: "PipelineRun";
  id: string;
  status: PipelineRunStatus;
  assets: JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_assets[];
  stats: JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results_stats;
}

export interface JobMetadataQuery_pipelineRunsOrError_PipelineRuns {
  __typename: "PipelineRuns";
  results: JobMetadataQuery_pipelineRunsOrError_PipelineRuns_results[];
}

export type JobMetadataQuery_pipelineRunsOrError = JobMetadataQuery_pipelineRunsOrError_InvalidPipelineRunsFilterError | JobMetadataQuery_pipelineRunsOrError_PipelineRuns;

export interface JobMetadataQuery {
  pipelineOrError: JobMetadataQuery_pipelineOrError;
  pipelineRunsOrError: JobMetadataQuery_pipelineRunsOrError;
}

export interface JobMetadataQueryVariables {
  params: PipelineSelector;
  runsFilter?: PipelineRunsFilter | null;
}
