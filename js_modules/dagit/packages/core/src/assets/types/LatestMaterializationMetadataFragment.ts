/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: LatestMaterializationMetadataFragment
// ====================================================

export interface LatestMaterializationMetadataFragment_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface LatestMaterializationMetadataFragment_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface LatestMaterializationMetadataFragment_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: LatestMaterializationMetadataFragment_runOrError_Run_repositoryOrigin | null;
}

export type LatestMaterializationMetadataFragment_runOrError = LatestMaterializationMetadataFragment_runOrError_RunNotFoundError | LatestMaterializationMetadataFragment_runOrError_Run;

export interface LatestMaterializationMetadataFragment_materializationEvent_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries = LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface LatestMaterializationMetadataFragment_materializationEvent_materialization {
  __typename: "Materialization";
  metadataEntries: LatestMaterializationMetadataFragment_materializationEvent_materialization_metadataEntries[];
}

export interface LatestMaterializationMetadataFragment_materializationEvent_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LatestMaterializationMetadataFragment_materializationEvent_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: LatestMaterializationMetadataFragment_materializationEvent_assetLineage_assetKey;
  partitions: string[];
}

export interface LatestMaterializationMetadataFragment_materializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: LatestMaterializationMetadataFragment_materializationEvent_stepStats;
  materialization: LatestMaterializationMetadataFragment_materializationEvent_materialization;
  assetLineage: LatestMaterializationMetadataFragment_materializationEvent_assetLineage[];
}

export interface LatestMaterializationMetadataFragment {
  __typename: "AssetMaterialization";
  partition: string | null;
  runOrError: LatestMaterializationMetadataFragment_runOrError;
  materializationEvent: LatestMaterializationMetadataFragment_materializationEvent;
}
