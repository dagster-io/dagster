// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PartitionBackfillParams, EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: LaunchPartitionBackfill
// ====================================================

export interface LaunchPartitionBackfill_launchPartitionBackfill_InvalidStepError {
  __typename: "InvalidStepError" | "InvalidOutputError" | "PipelineNotFoundError" | "PipelineRunConflict" | "PresetNotFoundError" | "ConflictingExecutionParamsError";
}

export interface LaunchPartitionBackfill_launchPartitionBackfill_PartitionBackfillSuccess {
  __typename: "PartitionBackfillSuccess";
  backfillId: string;
}

export interface LaunchPartitionBackfill_launchPartitionBackfill_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError";
  message: string;
}

export interface LaunchPartitionBackfill_launchPartitionBackfill_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LaunchPartitionBackfill_launchPartitionBackfill_PipelineConfigValidationInvalid_errors {
  __typename: "RuntimeMismatchConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "SelectorTypeConfigError";
  message: string;
  path: string[];
  reason: EvaluationErrorReason;
}

export interface LaunchPartitionBackfill_launchPartitionBackfill_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  pipelineName: string;
  errors: LaunchPartitionBackfill_launchPartitionBackfill_PipelineConfigValidationInvalid_errors[];
}

export type LaunchPartitionBackfill_launchPartitionBackfill = LaunchPartitionBackfill_launchPartitionBackfill_InvalidStepError | LaunchPartitionBackfill_launchPartitionBackfill_PartitionBackfillSuccess | LaunchPartitionBackfill_launchPartitionBackfill_PartitionSetNotFoundError | LaunchPartitionBackfill_launchPartitionBackfill_PythonError | LaunchPartitionBackfill_launchPartitionBackfill_PipelineConfigValidationInvalid;

export interface LaunchPartitionBackfill {
  launchPartitionBackfill: LaunchPartitionBackfill_launchPartitionBackfill;
}

export interface LaunchPartitionBackfillVariables {
  backfillParams: PartitionBackfillParams;
}
