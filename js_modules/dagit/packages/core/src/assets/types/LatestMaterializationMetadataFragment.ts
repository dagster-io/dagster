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

export interface LatestMaterializationMetadataFragment_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LatestMaterializationMetadataFragment_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LatestMaterializationMetadataFragment_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry_table;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LatestMaterializationMetadataFragment_metadataEntries = LatestMaterializationMetadataFragment_metadataEntries_PathMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_JsonMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_UrlMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_TextMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_MarkdownMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_PythonArtifactMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_FloatMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_IntMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_BoolMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_PipelineRunMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_AssetMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_TableMetadataEntry | LatestMaterializationMetadataFragment_metadataEntries_TableSchemaMetadataEntry;

export interface LatestMaterializationMetadataFragment_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LatestMaterializationMetadataFragment_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: LatestMaterializationMetadataFragment_assetLineage_assetKey;
  partitions: string[];
}

export interface LatestMaterializationMetadataFragment {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: LatestMaterializationMetadataFragment_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  metadataEntries: LatestMaterializationMetadataFragment_metadataEntries[];
  assetLineage: LatestMaterializationMetadataFragment_assetLineage[];
}
