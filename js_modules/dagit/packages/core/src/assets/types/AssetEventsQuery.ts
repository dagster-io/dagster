/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetEventsQuery
// ====================================================

export interface AssetEventsQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetEventsQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError = AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError_RunNotFoundError | AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError_Run;

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry_table;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries = AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_PathMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_JsonMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_UrlMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TextMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_MarkdownMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_PythonArtifactMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_FloatMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_IntMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_BoolMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_PipelineRunMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_AssetMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries_TableSchemaMetadataEntry;

export interface AssetEventsQuery_assetOrError_Asset_assetObservations {
  __typename: "ObservationEvent";
  partition: string | null;
  runOrError: AssetEventsQuery_assetOrError_Asset_assetObservations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: AssetEventsQuery_assetOrError_Asset_assetObservations_metadataEntries[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError = AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError_RunNotFoundError | AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run;

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry_table;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries = AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_PathMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_JsonMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_UrlMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TextMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_MarkdownMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_FloatMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_IntMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_BoolMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_PipelineRunMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_AssetMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableMetadataEntry | AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_TableSchemaMetadataEntry;

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetEventsQuery_assetOrError_Asset_assetMaterializations_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetEventsQuery_assetOrError_Asset_assetMaterializations {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetEventsQuery_assetOrError_Asset_assetMaterializations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: AssetEventsQuery_assetOrError_Asset_assetMaterializations_metadataEntries[];
  assetLineage: AssetEventsQuery_assetOrError_Asset_assetMaterializations_assetLineage[];
}

export interface AssetEventsQuery_assetOrError_Asset_definition {
  __typename: "AssetNode";
  id: string;
  partitionKeys: string[];
}

export interface AssetEventsQuery_assetOrError_Asset {
  __typename: "Asset";
  id: string;
  key: AssetEventsQuery_assetOrError_Asset_key;
  assetObservations: AssetEventsQuery_assetOrError_Asset_assetObservations[];
  assetMaterializations: AssetEventsQuery_assetOrError_Asset_assetMaterializations[];
  definition: AssetEventsQuery_assetOrError_Asset_definition | null;
}

export type AssetEventsQuery_assetOrError = AssetEventsQuery_assetOrError_AssetNotFoundError | AssetEventsQuery_assetOrError_Asset;

export interface AssetEventsQuery {
  assetOrError: AssetEventsQuery_assetOrError;
}

export interface AssetEventsQueryVariables {
  assetKey: AssetKeyInput;
  limit?: number | null;
  before?: string | null;
  partitionInLast?: number | null;
}
