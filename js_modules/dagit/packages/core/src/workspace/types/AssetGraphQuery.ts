// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphQuery
// ====================================================

export interface AssetGraphQuery_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface AssetGraphQuery_repositoryOrError_Repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_dependencies_upstreamAsset_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_dependencies_upstreamAsset {
  __typename: "AssetDefinition";
  id: string;
  assetKey: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_dependencies_upstreamAsset_assetKey;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_dependencies {
  __typename: "AssetDependency";
  inputName: string;
  upstreamAsset: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_dependencies_upstreamAsset;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization {
  __typename: "Materialization";
  metadataEntries: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  materialization: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_materialization;
  stepStats: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent_stepStats;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_runOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_runOrError_PipelineRun {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  status: PipelineRunStatus;
  pipelineName: string;
  mode: string;
}

export type AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_runOrError = AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_runOrError_PipelineRunNotFoundError | AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_runOrError_PipelineRun;

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations {
  __typename: "AssetMaterialization";
  materializationEvent: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_materializationEvent;
  runOrError: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations_runOrError;
}

export interface AssetGraphQuery_repositoryOrError_Repository_assetDefinitions {
  __typename: "AssetDefinition";
  id: string;
  assetKey: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetKey;
  opName: string | null;
  description: string | null;
  jobName: string | null;
  dependencies: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_dependencies[];
  assetMaterializations: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions_assetMaterializations[];
}

export interface AssetGraphQuery_repositoryOrError_Repository_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  modes: AssetGraphQuery_repositoryOrError_Repository_pipelines_modes[];
}

export interface AssetGraphQuery_repositoryOrError_Repository_schedules {
  __typename: "Schedule";
  id: string;
  name: string;
  pipelineName: string;
  mode: string;
  cronSchedule: string;
}

export interface AssetGraphQuery_repositoryOrError_Repository_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  pipelineName: string | null;
  mode: string | null;
}

export interface AssetGraphQuery_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetGraphQuery_repositoryOrError_Repository_location;
  assetDefinitions: AssetGraphQuery_repositoryOrError_Repository_assetDefinitions[];
  pipelines: AssetGraphQuery_repositoryOrError_Repository_pipelines[];
  schedules: AssetGraphQuery_repositoryOrError_Repository_schedules[];
  sensors: AssetGraphQuery_repositoryOrError_Repository_sensors[];
}

export type AssetGraphQuery_repositoryOrError = AssetGraphQuery_repositoryOrError_PythonError | AssetGraphQuery_repositoryOrError_Repository;

export interface AssetGraphQuery {
  repositoryOrError: AssetGraphQuery_repositoryOrError;
}

export interface AssetGraphQueryVariables {
  repositorySelector: RepositorySelector;
}
