/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetNodeFragment
// ====================================================

export interface AssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetNodeFragment_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetNodeFragment_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetNodeFragment_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetNodeFragment_assetMaterializations_runOrError = AssetNodeFragment_assetMaterializations_runOrError_RunNotFoundError | AssetNodeFragment_assetMaterializations_runOrError_Run;

export interface AssetNodeFragment_assetMaterializations_materializationEvent_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries = AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetNodeFragment_assetMaterializations_materializationEvent_materialization {
  __typename: "Materialization";
  metadataEntries: AssetNodeFragment_assetMaterializations_materializationEvent_materialization_metadataEntries[];
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetNodeFragment_assetMaterializations_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetNodeFragment_assetMaterializations_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetNodeFragment_assetMaterializations_materializationEvent_stepStats;
  materialization: AssetNodeFragment_assetMaterializations_materializationEvent_materialization;
  assetLineage: AssetNodeFragment_assetMaterializations_materializationEvent_assetLineage[];
}

export interface AssetNodeFragment_assetMaterializations {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetNodeFragment_assetMaterializations_runOrError;
  materializationEvent: AssetNodeFragment_assetMaterializations_materializationEvent;
}

export interface AssetNodeFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  jobName: string | null;
  assetKey: AssetNodeFragment_assetKey;
  assetMaterializations: AssetNodeFragment_assetMaterializations[];
}
