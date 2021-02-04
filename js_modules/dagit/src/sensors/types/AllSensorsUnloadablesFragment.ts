// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobType, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AllSensorsUnloadablesFragment
// ====================================================

export interface AllSensorsUnloadablesFragment_JobStates_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface AllSensorsUnloadablesFragment_JobStates_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: AllSensorsUnloadablesFragment_JobStates_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface AllSensorsUnloadablesFragment_JobStates_results_jobSpecificData_SensorJobData {
  __typename: "SensorJobData";
  lastRunKey: string | null;
}

export interface AllSensorsUnloadablesFragment_JobStates_results_jobSpecificData_ScheduleJobData {
  __typename: "ScheduleJobData";
  cronSchedule: string;
}

export type AllSensorsUnloadablesFragment_JobStates_results_jobSpecificData = AllSensorsUnloadablesFragment_JobStates_results_jobSpecificData_SensorJobData | AllSensorsUnloadablesFragment_JobStates_results_jobSpecificData_ScheduleJobData;

export interface AllSensorsUnloadablesFragment_JobStates_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
}

export interface AllSensorsUnloadablesFragment_JobStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsUnloadablesFragment_JobStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsUnloadablesFragment_JobStates_results_ticks_error_cause | null;
}

export interface AllSensorsUnloadablesFragment_JobStates_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  error: AllSensorsUnloadablesFragment_JobStates_results_ticks_error | null;
}

export interface AllSensorsUnloadablesFragment_JobStates_results {
  __typename: "JobState";
  id: string;
  name: string;
  jobType: JobType;
  status: JobStatus;
  repositoryOrigin: AllSensorsUnloadablesFragment_JobStates_results_repositoryOrigin;
  jobSpecificData: AllSensorsUnloadablesFragment_JobStates_results_jobSpecificData | null;
  runs: AllSensorsUnloadablesFragment_JobStates_results_runs[];
  ticks: AllSensorsUnloadablesFragment_JobStates_results_ticks[];
  runningCount: number;
}

export interface AllSensorsUnloadablesFragment_JobStates {
  __typename: "JobStates";
  results: AllSensorsUnloadablesFragment_JobStates_results[];
}

export interface AllSensorsUnloadablesFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AllSensorsUnloadablesFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AllSensorsUnloadablesFragment_PythonError_cause | null;
}

export type AllSensorsUnloadablesFragment = AllSensorsUnloadablesFragment_JobStates | AllSensorsUnloadablesFragment_PythonError;
