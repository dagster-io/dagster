// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: FetchScheduleYaml
// ====================================================

export interface FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinitionNotFoundError {
  __typename: "ScheduleDefinitionNotFoundError" | "PythonError";
}

export interface FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError_ScheduleRunConfig {
  __typename: "ScheduleRunConfig";
  yaml: string;
}

export interface FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError_PythonError_cause | null;
}

export type FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError = FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError_ScheduleRunConfig | FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError_PythonError;

export interface FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition {
  __typename: "ScheduleDefinition";
  runConfigOrError: FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition_runConfigOrError | null;
}

export type FetchScheduleYaml_scheduleDefinitionOrError = FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinitionNotFoundError | FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition;

export interface FetchScheduleYaml {
  scheduleDefinitionOrError: FetchScheduleYaml_scheduleDefinitionOrError;
}

export interface FetchScheduleYamlVariables {
  scheduleSelector: ScheduleSelector;
}
