/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeFragment
// ====================================================

export interface AssetNodeFragment_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeFragment_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeFragment_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeFragment_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeFragment_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeFragment_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeFragment_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeFragment_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeFragment_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeFragment_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeFragment_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeFragment_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeFragment_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetNodeFragment_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeFragment_metadataEntries_TableMetadataEntry_table;
}

export interface AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetNodeFragment_metadataEntries = AssetNodeFragment_metadataEntries_PathMetadataEntry | AssetNodeFragment_metadataEntries_JsonMetadataEntry | AssetNodeFragment_metadataEntries_UrlMetadataEntry | AssetNodeFragment_metadataEntries_TextMetadataEntry | AssetNodeFragment_metadataEntries_MarkdownMetadataEntry | AssetNodeFragment_metadataEntries_PythonArtifactMetadataEntry | AssetNodeFragment_metadataEntries_FloatMetadataEntry | AssetNodeFragment_metadataEntries_IntMetadataEntry | AssetNodeFragment_metadataEntries_PipelineRunMetadataEntry | AssetNodeFragment_metadataEntries_AssetMetadataEntry | AssetNodeFragment_metadataEntries_TableMetadataEntry | AssetNodeFragment_metadataEntries_TableSchemaMetadataEntry;

export interface AssetNodeFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeFragment_repository_location;
}

export interface AssetNodeFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  metadataEntries: AssetNodeFragment_metadataEntries[];
  partitionDefinition: string | null;
  assetKey: AssetNodeFragment_assetKey;
  repository: AssetNodeFragment_repository;
}
