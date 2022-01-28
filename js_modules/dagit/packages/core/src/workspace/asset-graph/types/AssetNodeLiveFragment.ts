/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetNodeLiveFragment
// ====================================================

export interface AssetNodeLiveFragment_latestMaterialization_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetNodeLiveFragment_latestMaterialization_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetNodeLiveFragment_latestMaterialization_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetNodeLiveFragment_latestMaterialization_runOrError = AssetNodeLiveFragment_latestMaterialization_runOrError_RunNotFoundError | AssetNodeLiveFragment_latestMaterialization_runOrError_Run;

export interface AssetNodeLiveFragment_latestMaterialization_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetNodeLiveFragment_latestMaterialization_metadataEntries = AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventTableSchemaMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventPathMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventJsonMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventUrlMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventTextMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventMarkdownMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventFloatMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventIntMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeLiveFragment_latestMaterialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetNodeLiveFragment_latestMaterialization_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_latestMaterialization_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetNodeLiveFragment_latestMaterialization_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetNodeLiveFragment_latestMaterialization {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetNodeLiveFragment_latestMaterialization_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetNodeLiveFragment_latestMaterialization_stepStats;
  metadataEntries: AssetNodeLiveFragment_latestMaterialization_metadataEntries[];
  assetLineage: AssetNodeLiveFragment_latestMaterialization_assetLineage[];
}

export interface AssetNodeLiveFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  latestMaterialization: AssetNodeLiveFragment_latestMaterialization | null;
}
