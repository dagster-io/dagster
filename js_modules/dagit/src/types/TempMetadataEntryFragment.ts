// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: TempMetadataEntryFragment
// ====================================================

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

export type TempMetadataEntryFragment = TempMetadataEntryFragment_EventPathMetadataEntry | TempMetadataEntryFragment_EventJsonMetadataEntry | TempMetadataEntryFragment_EventUrlMetadataEntry | TempMetadataEntryFragment_EventTextMetadataEntry;
