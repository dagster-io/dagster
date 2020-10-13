// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TempMetadataEntryFragment
// ====================================================

export interface TempMetadataEntryFragment_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry" | "EventIntMetadataEntry";
  label: string;
  description: string | null;
}

export interface TempMetadataEntryFragment_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface TempMetadataEntryFragment_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface TempMetadataEntryFragment_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface TempMetadataEntryFragment_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface TempMetadataEntryFragment_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface TempMetadataEntryFragment_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type TempMetadataEntryFragment = TempMetadataEntryFragment_EventFloatMetadataEntry | TempMetadataEntryFragment_EventPathMetadataEntry | TempMetadataEntryFragment_EventJsonMetadataEntry | TempMetadataEntryFragment_EventUrlMetadataEntry | TempMetadataEntryFragment_EventTextMetadataEntry | TempMetadataEntryFragment_EventMarkdownMetadataEntry | TempMetadataEntryFragment_EventPythonArtifactMetadataEntry;
