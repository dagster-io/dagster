// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleDefinitionFragment
// ====================================================

export interface ScheduleDefinitionFragment_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface ScheduleDefinitionFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface ScheduleDefinitionFragment_scheduleState_repositoryOrigin {
  __typename: "RepositoryOrigin";
  repositoryLocationName: string;
  repositoryName: string;
  repositoryLocationMetadata: ScheduleDefinitionFragment_scheduleState_repositoryOrigin_repositoryLocationMetadata[];
}

export interface ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
  id: string;
  pipelineName: string;
  status: PipelineRunStatus;
  runId: string;
}

export interface ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData {
  __typename: "ScheduleTickSuccessData";
  run: ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run | null;
}

export interface ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error_cause | null;
}

export interface ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData {
  __typename: "ScheduleTickFailureData";
  error: ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData_error;
}

export type ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData = ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData | ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickFailureData;

export interface ScheduleDefinitionFragment_scheduleState_ticks {
  __typename: "ScheduleTick";
  tickId: string;
  status: ScheduleTickStatus;
  timestamp: number;
  tickSpecificData: ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData | null;
}

export interface ScheduleDefinitionFragment_scheduleState_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ScheduleDefinitionFragment_scheduleState_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  tags: ScheduleDefinitionFragment_scheduleState_runs_tags[];
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface ScheduleDefinitionFragment_scheduleState {
  __typename: "ScheduleState";
  id: string;
  scheduleOriginId: string;
  repositoryOrigin: ScheduleDefinitionFragment_scheduleState_repositoryOrigin;
  repositoryOriginId: string;
  scheduleName: string;
  cronSchedule: string;
  runningScheduleCount: number;
  ticks: ScheduleDefinitionFragment_scheduleState_ticks[];
  runsCount: number;
  runs: ScheduleDefinitionFragment_scheduleState_runs[];
  ticksCount: number;
  status: ScheduleStatus;
}

export interface ScheduleDefinitionFragment_futureTicks_results {
  __typename: "ScheduleFutureTick";
  timestamp: number;
}

export interface ScheduleDefinitionFragment_futureTicks {
  __typename: "ScheduleFutureTicks";
  results: ScheduleDefinitionFragment_futureTicks_results[];
}

export interface ScheduleDefinitionFragment {
  __typename: "ScheduleDefinition";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: ScheduleDefinitionFragment_partitionSet | null;
  scheduleState: ScheduleDefinitionFragment_scheduleState | null;
  futureTicks: ScheduleDefinitionFragment_futureTicks;
}
