/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationType, InstigationStatus, RunStatus, InstigationTickStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: UnloadableSchedulesQuery
// ====================================================

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData {
  __typename: "SensorData";
  lastRunKey: string | null;
  lastCursor: string | null;
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData {
  __typename: "ScheduleData";
  cronSchedule: string;
}

export type UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData = UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_SensorData | UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData_ScheduleData;

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error_causes[];
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks {
  __typename: "InstigationTick";
  id: string;
  cursor: string | null;
  status: InstigationTickStatus;
  timestamp: number;
  skipReason: string | null;
  runIds: string[];
  runKeys: string[];
  error: UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks_error | null;
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  name: string;
  instigationType: InstigationType;
  status: InstigationStatus;
  repositoryName: string;
  repositoryLocationName: string;
  typeSpecificData: UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_typeSpecificData | null;
  runs: UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_runs[];
  ticks: UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results_ticks[];
  runningCount: number;
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates {
  __typename: "InstigationStates";
  results: UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates_results[];
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_PythonError_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface UnloadableSchedulesQuery_unloadableInstigationStatesOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: UnloadableSchedulesQuery_unloadableInstigationStatesOrError_PythonError_causes[];
}

export type UnloadableSchedulesQuery_unloadableInstigationStatesOrError = UnloadableSchedulesQuery_unloadableInstigationStatesOrError_InstigationStates | UnloadableSchedulesQuery_unloadableInstigationStatesOrError_PythonError;

export interface UnloadableSchedulesQuery {
  unloadableInstigationStatesOrError: UnloadableSchedulesQuery_unloadableInstigationStatesOrError;
}
