// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MetadataEntryFragment
// ====================================================

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
  floatValue: number;
}

export interface MetadataEntryFragment_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type MetadataEntryFragment = MetadataEntryFragment_EventPathMetadataEntry | MetadataEntryFragment_EventJsonMetadataEntry | MetadataEntryFragment_EventUrlMetadataEntry | MetadataEntryFragment_EventTextMetadataEntry | MetadataEntryFragment_EventMarkdownMetadataEntry | MetadataEntryFragment_EventPythonArtifactMetadataEntry | MetadataEntryFragment_EventFloatMetadataEntry | MetadataEntryFragment_EventIntMetadataEntry;
