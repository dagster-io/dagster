// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetMaterializationFragment
// ====================================================

export interface AssetMaterializationFragment_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetMaterializationFragment_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetMaterializationFragment_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetMaterializationFragment_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetMaterializationFragment_runOrError = AssetMaterializationFragment_runOrError_RunNotFoundError | AssetMaterializationFragment_runOrError_Run;

export interface AssetMaterializationFragment_materializationEvent_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type AssetMaterializationFragment_materializationEvent_materialization_metadataEntries = AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface AssetMaterializationFragment_materializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: AssetMaterializationFragment_materializationEvent_materialization_metadataEntries[];
}

export interface AssetMaterializationFragment_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationFragment_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetMaterializationFragment_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetMaterializationFragment_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetMaterializationFragment_materializationEvent_stepStats;
  materialization: AssetMaterializationFragment_materializationEvent_materialization;
  assetLineage: AssetMaterializationFragment_materializationEvent_assetLineage[];
}

export interface AssetMaterializationFragment {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: AssetMaterializationFragment_runOrError;
  materializationEvent: AssetMaterializationFragment_materializationEvent;
}
