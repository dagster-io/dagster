/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: UnloadableInstigationStatesQuery
// ====================================================

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData = UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData | UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData;

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_cause | null;
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error | null;
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData | null;
  runs: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs[];
  ticks: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks[];
  runningCount: number;
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_PythonError_cause | null;
}

export type UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError = UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_InstigationStates | UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError_PythonError;

export interface UnloadableInstigationStatesQuery {
  unloadableInstigationStatesOrError: UnloadableInstigationStatesQuery_unloadableInstigationStatesOrError;
}
