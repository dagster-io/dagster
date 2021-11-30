/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector, RunStatus } from "./../../../types/globalTypes";

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

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError = AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_RunNotFoundError | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError_Run;

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization {
  __typename: "Materialization";
  metadataEntries: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_stepStats;
  materialization: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_materialization;
  assetLineage: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent_assetLineage[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_runOrError;
  materializationEvent: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations_materializationEvent;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependedBy_asset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependedBy_asset {
  __typename: "AssetNode";
  id: string;
  assetKey: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependedBy_asset_assetKey;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependedBy {
  __typename: "AssetDependency";
  inputName: string;
  asset: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependedBy_asset;
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
  inputName: string;
  asset: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependencies_asset;
}

export interface AssetGraphQuery_pipelineOrError_Pipeline_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  jobName: string | null;
  assetKey: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetKey;
  assetMaterializations: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_assetMaterializations[];
  dependedBy: AssetGraphQuery_pipelineOrError_Pipeline_assetNodes_dependedBy[];
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
