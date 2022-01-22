/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, RepositorySelector, AssetKeyInput, RunStatus } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphLiveQuery
// ====================================================

export interface AssetGraphLiveQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface AssetGraphLiveQuery_repositoryOrError_Repository_inProgressRunsByStep_unstartedRuns {
  __typename: "Run";
  id: string;
}

export interface AssetGraphLiveQuery_repositoryOrError_Repository_inProgressRunsByStep_inProgressRuns {
  __typename: "Run";
  id: string;
}

export interface AssetGraphLiveQuery_repositoryOrError_Repository_inProgressRunsByStep {
  __typename: "InProgressRunsByStep";
  stepKey: string;
  unstartedRuns: AssetGraphLiveQuery_repositoryOrError_Repository_inProgressRunsByStep_unstartedRuns[];
  inProgressRuns: AssetGraphLiveQuery_repositoryOrError_Repository_inProgressRunsByStep_inProgressRuns[];
}

export interface AssetGraphLiveQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  inProgressRunsByStep: AssetGraphLiveQuery_repositoryOrError_Repository_inProgressRunsByStep[];
}

export type AssetGraphLiveQuery_repositoryOrError = AssetGraphLiveQuery_repositoryOrError_PythonError | AssetGraphLiveQuery_repositoryOrError_Repository;

export interface AssetGraphLiveQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError = AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_RunNotFoundError | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run;

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries = AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventPathMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventJsonMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventUrlMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventTextMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventFloatMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventIntMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry | AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries_EventAssetMetadataEntry;

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_stepStats;
  metadataEntries: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_metadataEntries[];
  assetLineage: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_assetLineage[];
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  assetMaterializations: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations[];
}

export interface AssetGraphLiveQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  id: string;
  assetNodes: AssetGraphLiveQuery_pipelineOrError_Pipeline_assetNodes[];
}

export type AssetGraphLiveQuery_pipelineOrError = AssetGraphLiveQuery_pipelineOrError_PipelineNotFoundError | AssetGraphLiveQuery_pipelineOrError_Pipeline;

export interface AssetGraphLiveQuery {
  repositoryOrError: AssetGraphLiveQuery_repositoryOrError;
  pipelineOrError: AssetGraphLiveQuery_pipelineOrError;
}

export interface AssetGraphLiveQueryVariables {
  pipelineSelector: PipelineSelector;
  repositorySelector: RepositorySelector;
  assetKeys?: AssetKeyInput[] | null;
}
