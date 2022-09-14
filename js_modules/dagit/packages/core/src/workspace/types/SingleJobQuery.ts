/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, RunStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SingleJobQuery
// ====================================================

export interface SingleJobQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface SingleJobQuery_pipelineOrError_Pipeline_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface SingleJobQuery_pipelineOrError_Pipeline_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface SingleJobQuery_pipelineOrError_Pipeline_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  scheduleState: SingleJobQuery_pipelineOrError_Pipeline_schedules_scheduleState;
}

export interface SingleJobQuery_pipelineOrError_Pipeline_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface SingleJobQuery_pipelineOrError_Pipeline_sensors {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  sensorState: SingleJobQuery_pipelineOrError_Pipeline_sensors_sensorState;
}

export interface SingleJobQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  description: string | null;
  runs: SingleJobQuery_pipelineOrError_Pipeline_runs[];
  schedules: SingleJobQuery_pipelineOrError_Pipeline_schedules[];
  sensors: SingleJobQuery_pipelineOrError_Pipeline_sensors[];
}

export type SingleJobQuery_pipelineOrError = SingleJobQuery_pipelineOrError_PipelineNotFoundError | SingleJobQuery_pipelineOrError_Pipeline;

export interface SingleJobQuery {
  pipelineOrError: SingleJobQuery_pipelineOrError;
}

export interface SingleJobQueryVariables {
  selector: PipelineSelector;
}
