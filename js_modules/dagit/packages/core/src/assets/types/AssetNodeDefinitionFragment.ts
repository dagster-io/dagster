/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetNodeDefinitionFragment
// ====================================================

export interface AssetNodeDefinitionFragment_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeDefinitionFragment_repository_location;
}

export interface AssetNodeDefinitionFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_latestMaterialization_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetNodeDefinitionFragment_latestMaterialization_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetNodeDefinitionFragment_latestMaterialization_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetNodeDefinitionFragment_latestMaterialization_runOrError = AssetNodeDefinitionFragment_latestMaterialization_runOrError_RunNotFoundError | AssetNodeDefinitionFragment_latestMaterialization_runOrError_Run;

export interface AssetNodeDefinitionFragment_latestMaterialization_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetNodeDefinitionFragment_latestMaterialization_metadataEntries = AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventPathMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventJsonMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventUrlMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventTextMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventFloatMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventIntMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeDefinitionFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetNodeDefinitionFragment_latestMaterialization_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_latestMaterialization_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetNodeDefinitionFragment_latestMaterialization_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetNodeDefinitionFragment_latestMaterialization {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetNodeDefinitionFragment_latestMaterialization_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetNodeDefinitionFragment_latestMaterialization_stepStats;
  metadataEntries: AssetNodeDefinitionFragment_latestMaterialization_metadataEntries[];
  assetLineage: AssetNodeDefinitionFragment_latestMaterialization_assetLineage[];
}

export interface AssetNodeDefinitionFragment_dependencies_asset_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_dependencies_asset_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeDefinitionFragment_dependencies_asset_repository_location;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError = AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError_RunNotFoundError | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError_Run;

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries = AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventPathMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventJsonMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventUrlMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventTextMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventFloatMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventIntMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_stepStats;
  metadataEntries: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_metadataEntries[];
  assetLineage: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization_assetLineage[];
}

export interface AssetNodeDefinitionFragment_dependencies_asset {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobs: AssetNodeDefinitionFragment_dependencies_asset_jobs[];
  description: string | null;
  partitionDefinition: string | null;
  assetKey: AssetNodeDefinitionFragment_dependencies_asset_assetKey;
  repository: AssetNodeDefinitionFragment_dependencies_asset_repository;
  latestMaterialization: AssetNodeDefinitionFragment_dependencies_asset_latestMaterialization | null;
}

export interface AssetNodeDefinitionFragment_dependencies {
  __typename: "AssetDependency";
  asset: AssetNodeDefinitionFragment_dependencies_asset;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_jobs {
  __typename: "Pipeline";
  id: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeDefinitionFragment_dependedBy_asset_repository_location;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError = AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError_RunNotFoundError | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError_Run;

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries = AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventPathMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventJsonMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventUrlMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventTextMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventFloatMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventIntMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_stepStats;
  metadataEntries: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_metadataEntries[];
  assetLineage: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization_assetLineage[];
}

export interface AssetNodeDefinitionFragment_dependedBy_asset {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  jobs: AssetNodeDefinitionFragment_dependedBy_asset_jobs[];
  description: string | null;
  partitionDefinition: string | null;
  assetKey: AssetNodeDefinitionFragment_dependedBy_asset_assetKey;
  repository: AssetNodeDefinitionFragment_dependedBy_asset_repository;
  latestMaterialization: AssetNodeDefinitionFragment_dependedBy_asset_latestMaterialization | null;
}

export interface AssetNodeDefinitionFragment_dependedBy {
  __typename: "AssetDependency";
  asset: AssetNodeDefinitionFragment_dependedBy_asset;
}

export interface AssetNodeDefinitionFragment {
  __typename: "AssetNode";
  id: string;
  description: string | null;
  opName: string | null;
  jobs: AssetNodeDefinitionFragment_jobs[];
  repository: AssetNodeDefinitionFragment_repository;
  partitionDefinition: string | null;
  assetKey: AssetNodeDefinitionFragment_assetKey;
  latestMaterialization: AssetNodeDefinitionFragment_latestMaterialization | null;
  dependencies: AssetNodeDefinitionFragment_dependencies[];
  dependedBy: AssetNodeDefinitionFragment_dependedBy[];
}
