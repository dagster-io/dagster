// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { SensorSelector, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorRootQuery
// ====================================================

export interface SensorRootQuery_sensorOrError_SensorNotFoundError {
  __typename: "SensorNotFoundError" | "PythonError";
}

export interface SensorRootQuery_sensorOrError_Sensor_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SensorRootQuery_sensorOrError_Sensor_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface SensorRootQuery_sensorOrError_Sensor {
  __typename: "Sensor";
  id: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  status: JobStatus;
  runs: SensorRootQuery_sensorOrError_Sensor_runs[];
  ticks: SensorRootQuery_sensorOrError_Sensor_ticks[];
}

export type SensorRootQuery_sensorOrError = SensorRootQuery_sensorOrError_SensorNotFoundError | SensorRootQuery_sensorOrError_Sensor;

export interface SensorRootQuery {
  sensorOrError: SensorRootQuery_sensorOrError;
}

export interface SensorRootQueryVariables {
  sensorSelector: SensorSelector;
}
