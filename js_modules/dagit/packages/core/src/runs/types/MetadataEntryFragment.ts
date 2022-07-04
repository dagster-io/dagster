/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: MetadataEntryFragment
// ====================================================

export interface MetadataEntryFragment_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface MetadataEntryFragment_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface MetadataEntryFragment_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface MetadataEntryFragment_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface MetadataEntryFragment_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface MetadataEntryFragment_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface MetadataEntryFragment_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface MetadataEntryFragment_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface MetadataEntryFragment_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface MetadataEntryFragment_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface MetadataEntryFragment_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface MetadataEntryFragment_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: MetadataEntryFragment_AssetMetadataEntry_assetKey;
}

export interface MetadataEntryFragment_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface MetadataEntryFragment_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: MetadataEntryFragment_TableMetadataEntry_table_schema_columns_constraints;
}

export interface MetadataEntryFragment_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface MetadataEntryFragment_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: MetadataEntryFragment_TableMetadataEntry_table_schema_columns[];
  constraints: MetadataEntryFragment_TableMetadataEntry_table_schema_constraints | null;
}

export interface MetadataEntryFragment_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: MetadataEntryFragment_TableMetadataEntry_table_schema;
}

export interface MetadataEntryFragment_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: MetadataEntryFragment_TableMetadataEntry_table;
}

export interface MetadataEntryFragment_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface MetadataEntryFragment_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: MetadataEntryFragment_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface MetadataEntryFragment_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface MetadataEntryFragment_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: MetadataEntryFragment_TableSchemaMetadataEntry_schema_columns[];
  constraints: MetadataEntryFragment_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface MetadataEntryFragment_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: MetadataEntryFragment_TableSchemaMetadataEntry_schema;
}

export type MetadataEntryFragment = MetadataEntryFragment_PathMetadataEntry | MetadataEntryFragment_JsonMetadataEntry | MetadataEntryFragment_UrlMetadataEntry | MetadataEntryFragment_TextMetadataEntry | MetadataEntryFragment_MarkdownMetadataEntry | MetadataEntryFragment_PythonArtifactMetadataEntry | MetadataEntryFragment_FloatMetadataEntry | MetadataEntryFragment_IntMetadataEntry | MetadataEntryFragment_BoolMetadataEntry | MetadataEntryFragment_PipelineRunMetadataEntry | MetadataEntryFragment_AssetMetadataEntry | MetadataEntryFragment_TableMetadataEntry | MetadataEntryFragment_TableSchemaMetadataEntry;
