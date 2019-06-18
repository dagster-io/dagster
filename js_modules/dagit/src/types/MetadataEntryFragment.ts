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

export type MetadataEntryFragment = MetadataEntryFragment_EventPathMetadataEntry | MetadataEntryFragment_EventJsonMetadataEntry;
