/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetObservationFragment
// ====================================================

export interface AssetObservationFragment_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetObservationFragment_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetObservationFragment_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetObservationFragment_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetObservationFragment_runOrError = AssetObservationFragment_runOrError_RunNotFoundError | AssetObservationFragment_runOrError_Run;

export interface AssetObservationFragment_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetObservationFragment_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetObservationFragment_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetObservationFragment_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetObservationFragment_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetObservationFragment_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetObservationFragment_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetObservationFragment_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetObservationFragment_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetObservationFragment_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetObservationFragment_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetObservationFragment_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetObservationFragment_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetObservationFragment_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetObservationFragment_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetObservationFragment_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetObservationFragment_metadataEntries_TableMetadataEntry_table;
}

export interface AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetObservationFragment_metadataEntries = AssetObservationFragment_metadataEntries_PathMetadataEntry | AssetObservationFragment_metadataEntries_JsonMetadataEntry | AssetObservationFragment_metadataEntries_UrlMetadataEntry | AssetObservationFragment_metadataEntries_TextMetadataEntry | AssetObservationFragment_metadataEntries_MarkdownMetadataEntry | AssetObservationFragment_metadataEntries_PythonArtifactMetadataEntry | AssetObservationFragment_metadataEntries_FloatMetadataEntry | AssetObservationFragment_metadataEntries_IntMetadataEntry | AssetObservationFragment_metadataEntries_BoolMetadataEntry | AssetObservationFragment_metadataEntries_PipelineRunMetadataEntry | AssetObservationFragment_metadataEntries_AssetMetadataEntry | AssetObservationFragment_metadataEntries_TableMetadataEntry | AssetObservationFragment_metadataEntries_TableSchemaMetadataEntry;

export interface AssetObservationFragment {
  __typename: "ObservationEvent";
  partition: string | null;
  runOrError: AssetObservationFragment_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: AssetObservationFragment_metadataEntries[];
}
