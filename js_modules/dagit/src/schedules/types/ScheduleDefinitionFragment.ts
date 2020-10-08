// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleTickStatus, PipelineRunStatus, ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleDefinitionFragment
// ====================================================

export interface ScheduleDefinitionFragment_partitionSet {
  __typename: "PartitionSet";
  name: string;
}

export interface ScheduleDefinitionFragment_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata {
  __typename: "CodePointerMetadata";
  key: string;
  value: string;
}

export interface ScheduleDefinitionFragment_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer {
  __typename: "CodePointer";
  metadata: ScheduleDefinitionFragment_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer_metadata[];
}

export interface ScheduleDefinitionFragment_scheduleState_repositoryOrigin_PythonRepositoryOrigin {
  __typename: "PythonRepositoryOrigin";
  codePointer: ScheduleDefinitionFragment_scheduleState_repositoryOrigin_PythonRepositoryOrigin_codePointer;
  executablePath: string;
}

export interface ScheduleDefinitionFragment_scheduleState_repositoryOrigin_GrpcRepositoryOrigin {
  __typename: "GrpcRepositoryOrigin";
  grpcUrl: string;
}

export type ScheduleDefinitionFragment_scheduleState_repositoryOrigin = ScheduleDefinitionFragment_scheduleState_repositoryOrigin_PythonRepositoryOrigin | ScheduleDefinitionFragment_scheduleState_repositoryOrigin_GrpcRepositoryOrigin;

export interface ScheduleDefinitionFragment_scheduleState_ticks_tickSpecificData_ScheduleTickSuccessData_run {
  __typename: "PipelineRun";
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

export interface ScheduleDefinitionFragment {
  __typename: "ScheduleDefinition";
  name: string;
  cronSchedule: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  partitionSet: ScheduleDefinitionFragment_partitionSet | null;
  scheduleState: ScheduleDefinitionFragment_scheduleState | null;
}
