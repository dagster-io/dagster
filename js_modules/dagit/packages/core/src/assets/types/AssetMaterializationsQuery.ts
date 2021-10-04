// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetMaterializationsQuery
// ====================================================

export interface AssetMaterializationsQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetMaterializationsQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun {
  __typename: "PipelineRun";
  id: string;
  runId: string;
  mode: string;
  status: PipelineRunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError = AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRunNotFoundError | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun;

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_stepStats {
  __typename: "PipelineRunStepStats";
  endTime: number | null;
  startTime: number | null;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_stepStats;
  materialization: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization;
  assetLineage: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent_assetLineage[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError;
  materializationEvent: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_materializationEvent;
}

export interface AssetMaterializationsQuery_assetOrError_Asset {
  __typename: "Asset";
  id: string;
  key: AssetMaterializationsQuery_assetOrError_Asset_key;
  assetMaterializations: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations[];
}

export type AssetMaterializationsQuery_assetOrError = AssetMaterializationsQuery_assetOrError_AssetNotFoundError | AssetMaterializationsQuery_assetOrError_Asset;

export interface AssetMaterializationsQuery {
  assetOrError: AssetMaterializationsQuery_assetOrError;
}

export interface AssetMaterializationsQueryVariables {
  assetKey: AssetKeyInput;
  limit: number;
  before?: string | null;
}
