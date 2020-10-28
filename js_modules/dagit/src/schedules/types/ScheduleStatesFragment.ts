// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleStatesFragment
// ====================================================

export interface ScheduleStatesFragment_results_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduleStatesFragment_results_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduleStatesFragment_results_repositoryOrigin_repositoryLocationMetadata[];
}

export interface ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type ScheduleStatesFragment_results_ticks_tickSpecificData = ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickSuccessData | ScheduleStatesFragment_results_ticks_tickSpecificData_ScheduleTickFailureData;

export interface ScheduleStatesFragment_results_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: ScheduleStatesFragment_results_ticks_tickSpecificData | null;
}

export interface ScheduleStatesFragment_results_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleStatesFragment_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: ScheduleStatesFragment_results_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface ScheduleStatesFragment_results {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: ScheduleStatesFragment_results_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: ScheduleStatesFragment_results_ticks[];
  runsCount: number;
  runs: ScheduleStatesFragment_results_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface ScheduleStatesFragment {
  __typename: "ScheduleStates";
  results: ScheduleStatesFragment_results[];
}
