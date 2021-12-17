/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MetadataEntryFragment
// ====================================================

export interface MetadataEntryFragment_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface MetadataEntryFragment_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface MetadataEntryFragment_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface MetadataEntryFragment_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface MetadataEntryFragment_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface MetadataEntryFragment_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface MetadataEntryFragment_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface MetadataEntryFragment_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface MetadataEntryFragment_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface MetadataEntryFragment_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface MetadataEntryFragment_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface MetadataEntryFragment_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: MetadataEntryFragment_EventAssetMetadataEntry_assetKey;
}

export type MetadataEntryFragment = MetadataEntryFragment_EventTableSchemaMetadataEntry | MetadataEntryFragment_EventPathMetadataEntry | MetadataEntryFragment_EventJsonMetadataEntry | MetadataEntryFragment_EventUrlMetadataEntry | MetadataEntryFragment_EventTextMetadataEntry | MetadataEntryFragment_EventMarkdownMetadataEntry | MetadataEntryFragment_EventPythonArtifactMetadataEntry | MetadataEntryFragment_EventFloatMetadataEntry | MetadataEntryFragment_EventIntMetadataEntry | MetadataEntryFragment_EventPipelineRunMetadataEntry | MetadataEntryFragment_EventAssetMetadataEntry;
