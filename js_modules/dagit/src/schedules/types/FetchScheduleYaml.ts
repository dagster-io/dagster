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

export interface FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition {
  __typename: "ScheduleDefinition";
  runConfigYaml: string | null;
}

export type FetchScheduleYaml_scheduleDefinitionOrError = FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinitionNotFoundError | FetchScheduleYaml_scheduleDefinitionOrError_ScheduleDefinition;

export interface FetchScheduleYaml {
  scheduleDefinitionOrError: FetchScheduleYaml_scheduleDefinitionOrError;
}

export interface FetchScheduleYamlVariables {
  scheduleSelector: ScheduleSelector;
}
