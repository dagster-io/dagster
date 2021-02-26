// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AllSchedulesUnloadablesFragment
// ====================================================

export interface AllSchedulesUnloadablesFragment_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSchedulesUnloadablesFragment_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSchedulesUnloadablesFragment_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSchedulesUnloadablesFragment_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSchedulesUnloadablesFragment_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSchedulesUnloadablesFragment_JobStates_results_jobSpecificData = AllSchedulesUnloadablesFragment_JobStates_results_jobSpecificData_SensorJobData | AllSchedulesUnloadablesFragment_JobStates_results_jobSpecificData_ScheduleJobData;

export interface AllSchedulesUnloadablesFragment_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSchedulesUnloadablesFragment_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesUnloadablesFragment_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesUnloadablesFragment_JobStates_results_ticks_error_cause | null;
}

export interface AllSchedulesUnloadablesFragment_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSchedulesUnloadablesFragment_JobStates_results_ticks_error | null;
}

export interface AllSchedulesUnloadablesFragment_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSchedulesUnloadablesFragment_JobStates_results_repositoryOrigin;
  jobSpecificData: AllSchedulesUnloadablesFragment_JobStates_results_jobSpecificData | null;
  runs: AllSchedulesUnloadablesFragment_JobStates_results_runs[];
  ticks: AllSchedulesUnloadablesFragment_JobStates_results_ticks[];
  runningCount: number;
}

export interface AllSchedulesUnloadablesFragment_JobStates {
  __typename: "JobStates";
  results: AllSchedulesUnloadablesFragment_JobStates_results[];
}

export interface AllSchedulesUnloadablesFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSchedulesUnloadablesFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSchedulesUnloadablesFragment_PythonError_cause | null;
}

export type AllSchedulesUnloadablesFragment = AllSchedulesUnloadablesFragment_JobStates | AllSchedulesUnloadablesFragment_PythonError;
