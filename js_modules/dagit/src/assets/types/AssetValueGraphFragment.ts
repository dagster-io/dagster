// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetValueGraphFragment
// ====================================================

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number;
}

export interface AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type AssetValueGraphFragment_materializationEvent_materialization_metadataEntries = AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventPathMetadataEntry | AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventTextMetadataEntry | AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | AssetValueGraphFragment_materializationEvent_materialization_metadataEntries_EventIntMetadataEntry;

export interface AssetValueGraphFragment_materializationEvent_materialization {
  __typename: "Materialization";
  metadataEntries: AssetValueGraphFragment_materializationEvent_materialization_metadataEntries[];
}

export interface AssetValueGraphFragment_materializationEvent {
  __typename: "StepMaterializationEvent";
  timestamp: string;
  materialization: AssetValueGraphFragment_materializationEvent_materialization;
}

export interface AssetValueGraphFragment {
  __typename: "AssetMaterialization";
  materializationEvent: AssetValueGraphFragment_materializationEvent;
}
