// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { AssetKeyInput, PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetQuery
// ====================================================

export interface AssetQuery_assetOrError_AssetsNotSupportedError {
  __typename: "AssetsNotSupportedError";
}

export interface AssetQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRunNotFoundError {
  __typename: "PipelineRunNotFoundError" | "PythonError";
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun_pipeline {
  __typename: "PipelineSnapshot" | "UnknownPipeline";
  name: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun {
  __typename: "PipelineRun";
  runId: string;
  tags: AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun_tags[];
  status: PipelineRunStatus;
  pipeline: AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun_pipeline;
}

export type AssetQuery_assetOrError_Asset_assetMaterializations_runOrError = AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRunNotFoundError | AssetQuery_assetOrError_Asset_assetMaterializations_runOrError_PipelineRun;

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry;

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  materialization: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent_materialization;
}

export interface AssetQuery_assetOrError_Asset_assetMaterializations {
  __typename: "AssetMaterialization";
  runOrError: AssetQuery_assetOrError_Asset_assetMaterializations_runOrError;
  materializationEvent: AssetQuery_assetOrError_Asset_assetMaterializations_materializationEvent;
}

export interface AssetQuery_assetOrError_Asset_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface AssetQuery_assetOrError_Asset_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
  endTime: number | null;
}

export interface AssetQuery_assetOrError_Asset_runs_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface AssetQuery_assetOrError_Asset_runs_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: AssetQuery_assetOrError_Asset_runs_stats_PythonError_cause | null;
}

export type AssetQuery_assetOrError_Asset_runs_stats = AssetQuery_assetOrError_Asset_runs_stats_PipelineRunStatsSnapshot | AssetQuery_assetOrError_Asset_runs_stats_PythonError;

export interface AssetQuery_assetOrError_Asset_runs {
  __typename: "PipelineRun";
  runId: string;
  status: PipelineRunStatus;
  stepKeysToExecute: string[] | null;
  canTerminate: boolean;
  mode: string;
  rootRunId: string | null;
  parentRunId: string | null;
  pipelineSnapshotId: string | null;
  pipelineName: string;
  solidSelection: string[] | null;
  tags: AssetQuery_assetOrError_Asset_runs_tags[];
  stats: AssetQuery_assetOrError_Asset_runs_stats;
}

export interface AssetQuery_assetOrError_Asset {
  __typename: "Asset";
  key: AssetQuery_assetOrError_Asset_key;
  assetMaterializations: AssetQuery_assetOrError_Asset_assetMaterializations[];
  runs: AssetQuery_assetOrError_Asset_runs[];
}

export type AssetQuery_assetOrError = AssetQuery_assetOrError_AssetsNotSupportedError | AssetQuery_assetOrError_Asset;

export interface AssetQuery {
  assetOrError: AssetQuery_assetOrError;
}

export interface AssetQueryVariables {
  assetKey: AssetKeyInput;
}
