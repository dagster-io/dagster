/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { EvaluationErrorReason } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPreviewConfigValidationFragment
// ====================================================

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationValid {
  __typename: "PipelineConfigValidationValid" | "PipelineNotFoundError";
}

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  reason: EvaluationErrorReason;
  message: string;
}

export interface RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid_errors[];
}

export type RunPreviewConfigValidationFragment = RunPreviewConfigValidationFragment_PipelineConfigValidationValid | RunPreviewConfigValidationFragment_PipelineConfigValidationInvalid;
