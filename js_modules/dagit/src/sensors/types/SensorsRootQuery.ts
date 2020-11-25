// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, JobStatus, PipelineRunStatus, JobTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SensorsRootQuery
// ====================================================

export interface SensorsRootQuery_sensorsOrError_RepositoryNotFoundError {
  __typename: "RepositoryNotFoundError";
}

export interface SensorsRootQuery_sensorsOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SensorsRootQuery_sensorsOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SensorsRootQuery_sensorsOrError_PythonError_cause | null;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_runs {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  pipelineName: string;
  status: PipelineRunStatus;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results_ticks {
  __typename: "JobTick";
  id: string;
  status: JobTickStatus;
  timestamp: number;
}

export interface SensorsRootQuery_sensorsOrError_Sensors_results {
  __typename: "Sensor";
  id: string;
  name: string;
  pipelineName: string;
  solidSelection: (string | null)[] | null;
  mode: string;
  status: JobStatus;
  runs: SensorsRootQuery_sensorsOrError_Sensors_results_runs[];
  ticks: SensorsRootQuery_sensorsOrError_Sensors_results_ticks[];
}

export interface SensorsRootQuery_sensorsOrError_Sensors {
  __typename: "Sensors";
  results: SensorsRootQuery_sensorsOrError_Sensors_results[];
}

export type SensorsRootQuery_sensorsOrError = SensorsRootQuery_sensorsOrError_RepositoryNotFoundError | SensorsRootQuery_sensorsOrError_PythonError | SensorsRootQuery_sensorsOrError_Sensors;

export interface SensorsRootQuery {
  sensorsOrError: SensorsRootQuery_sensorsOrError;
}

export interface SensorsRootQueryVariables {
  repositorySelector: RepositorySelector;
}
