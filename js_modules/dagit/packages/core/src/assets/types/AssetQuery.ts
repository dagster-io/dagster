/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetQuery
// ====================================================

export interface AssetQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  timestamp: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations {
  __typename: "AssetMaterialization";
  materializationEvent: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent;
}

export interface AssetQuery_assetOrError_Asset_definition_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_definition_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetQuery_assetOrError_Asset_definition_repository_location;
}

export interface AssetQuery_assetOrError_Asset_definition_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError = AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError_RunNotFoundError | AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError_Run;

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization {
  __typename: "MaterializationOrObservation";
  metadataEntries: AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_stepStats;
  materialization: AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_materialization;
  assetLineage: AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent_assetLineage[];
}

export interface AssetQuery_assetOrError_Asset_definition_assetMaterializations {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetQuery_assetOrError_Asset_definition_assetMaterializations_runOrError;
  materializationEvent: AssetQuery_assetOrError_Asset_definition_assetMaterializations_materializationEvent;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError = AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError_RunNotFoundError | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError_Run;

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization {
  __typename: "MaterializationOrObservation";
  metadataEntries: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_stepStats;
  materialization: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_materialization;
  assetLineage: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent_assetLineage[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_runOrError;
  materializationEvent: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations_materializationEvent;
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies_asset {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobs: AssetQuery_assetOrError_Asset_definition_dependencies_asset_jobs[];
  description: string | null;
  partitionDefinition: string | null;
  assetKey: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetKey;
  assetMaterializations: AssetQuery_assetOrError_Asset_definition_dependencies_asset_assetMaterializations[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependencies {
  __typename: "AssetDependency";
  asset: AssetQuery_assetOrError_Asset_definition_dependencies_asset;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError = AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError_RunNotFoundError | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError_Run;

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization {
  __typename: "MaterializationOrObservation";
  metadataEntries: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_stepStats;
  materialization: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_materialization;
  assetLineage: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent_assetLineage[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_runOrError;
  materializationEvent: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations_materializationEvent;
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy_asset {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobs: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_jobs[];
  description: string | null;
  partitionDefinition: string | null;
  assetKey: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetKey;
  assetMaterializations: AssetQuery_assetOrError_Asset_definition_dependedBy_asset_assetMaterializations[];
}

export interface AssetQuery_assetOrError_Asset_definition_dependedBy {
  __typename: "AssetDependency";
  asset: AssetQuery_assetOrError_Asset_definition_dependedBy_asset;
}

export interface AssetQuery_assetOrError_Asset_definition {
  __typename: "AssetNode";
  id: string;
  partitionDefinition: string | null;
  repository: AssetQuery_assetOrError_Asset_definition_repository;
  description: string | null;
  opName: string | null;
  jobs: AssetQuery_assetOrError_Asset_definition_jobs[];
  assetKey: AssetQuery_assetOrError_Asset_definition_assetKey;
  assetMaterializations: AssetQuery_assetOrError_Asset_definition_assetMaterializations[];
  dependencies: AssetQuery_assetOrError_Asset_definition_dependencies[];
  dependedBy: AssetQuery_assetOrError_Asset_definition_dependedBy[];
}

export interface AssetQuery_assetOrError_Asset {
  __typename: "Asset";
  id: string;
  key: AssetQuery_assetOrError_Asset_key;
  assetMaterializations: AssetQuery_assetOrError_Asset_assetMaterializations[];
  definition: AssetQuery_assetOrError_Asset_definition | null;
}

export type AssetQuery_assetOrError = AssetQuery_assetOrError_AssetNotFoundError | AssetQuery_assetOrError_Asset;

export interface AssetQuery {
  assetOrError: AssetQuery_assetOrError;
}

export interface AssetQueryVariables {
  assetKey: AssetKeyInput;
}
