// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ConfigPresetsQuery
// ====================================================

export interface ConfigPresetsQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface ConfigPresetsQuery_pipelineOrError_Pipeline_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSelection: string[] | null;
  runConfigYaml: string;
}

export interface ConfigPresetsQuery_pipelineOrError_Pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigPresetsQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  name: string;
  presets: ConfigPresetsQuery_pipelineOrError_Pipeline_presets[];
  tags: ConfigPresetsQuery_pipelineOrError_Pipeline_tags[];
}

export type ConfigPresetsQuery_pipelineOrError = ConfigPresetsQuery_pipelineOrError_PipelineNotFoundError | ConfigPresetsQuery_pipelineOrError_Pipeline;

export interface ConfigPresetsQuery {
  pipelineOrError: ConfigPresetsQuery_pipelineOrError;
}

export interface ConfigPresetsQueryVariables {
  pipelineSelector: PipelineSelector;
}
