/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphQuery
// ====================================================

export interface AssetGraphQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependencies_asset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependencies_asset {
  __typename: "AssetNode";
  id: string;
  assetKey: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependencies_asset_assetKey;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependencies {
  __typename: "AssetDependency";
  asset: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependencies_asset;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  jobName: string | null;
  assetKey: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetKey;
  dependencies: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependencies[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  assetNodes: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes[];
}

export type AssetGraphQuery_pipelineOrError = AssetGraphQuery_pipelineOrError_PipelineNotFoundError | AssetGraphQuery_pipelineOrError_Pipeline;

export interface AssetGraphQuery {
  pipelineOrError: AssetGraphQuery_pipelineOrError;
}

export interface AssetGraphQueryVariables {
  pipelineSelector: PipelineSelector;
}
