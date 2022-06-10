/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetMaterializationFragment
// ====================================================

export interface AssetMaterializationFragment_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetMaterializationFragment_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetMaterializationFragment_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetMaterializationFragment_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetMaterializationFragment_runOrError = AssetMaterializationFragment_runOrError_RunNotFoundError | AssetMaterializationFragment_runOrError_Run;

export interface AssetMaterializationFragment_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetMaterializationFragment_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetMaterializationFragment_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetMaterializationFragment_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetMaterializationFragment_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetMaterializationFragment_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetMaterializationFragment_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetMaterializationFragment_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetMaterializationFragment_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetMaterializationFragment_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetMaterializationFragment_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationFragment_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetMaterializationFragment_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetMaterializationFragment_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetMaterializationFragment_metadataEntries_TableMetadataEntry_table;
}

export interface AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetMaterializationFragment_metadataEntries = AssetMaterializationFragment_metadataEntries_PathMetadataEntry | AssetMaterializationFragment_metadataEntries_JsonMetadataEntry | AssetMaterializationFragment_metadataEntries_UrlMetadataEntry | AssetMaterializationFragment_metadataEntries_TextMetadataEntry | AssetMaterializationFragment_metadataEntries_MarkdownMetadataEntry | AssetMaterializationFragment_metadataEntries_PythonArtifactMetadataEntry | AssetMaterializationFragment_metadataEntries_FloatMetadataEntry | AssetMaterializationFragment_metadataEntries_IntMetadataEntry | AssetMaterializationFragment_metadataEntries_BoolMetadataEntry | AssetMaterializationFragment_metadataEntries_PipelineRunMetadataEntry | AssetMaterializationFragment_metadataEntries_AssetMetadataEntry | AssetMaterializationFragment_metadataEntries_TableMetadataEntry | AssetMaterializationFragment_metadataEntries_TableSchemaMetadataEntry;

export interface AssetMaterializationFragment_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationFragment_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetMaterializationFragment_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetMaterializationFragment {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetMaterializationFragment_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: AssetMaterializationFragment_metadataEntries[];
  assetLineage: AssetMaterializationFragment_assetLineage[];
}
