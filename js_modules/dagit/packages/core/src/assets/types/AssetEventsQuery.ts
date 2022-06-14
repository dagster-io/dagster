/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetEventsQuery
// ====================================================

export interface AssetEventsQuery_materializedKeyOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError = AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError_RunNotFoundError | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError_Run;

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry_table;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries = AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_PathMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_JsonMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_UrlMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TextMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_MarkdownMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_PythonArtifactMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_FloatMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_IntMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_BoolMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_PipelineRunMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_AssetMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries_TableSchemaMetadataEntry;

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations {
  __typename: "ObservationEvent";
  partition: string | null;
  runOrError: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations_metadataEntries[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError = AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError_RunNotFoundError | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError_Run;

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry_table;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries = AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_PathMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_JsonMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_UrlMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TextMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_MarkdownMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_FloatMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_IntMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_BoolMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_PipelineRunMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_AssetMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableMetadataEntry | AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries_TableSchemaMetadataEntry;

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_metadataEntries[];
  assetLineage: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations_assetLineage[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey_definition {
  __typename: "AssetNode";
  id: string;
  partitionKeys: string[];
}

export interface AssetEventsQuery_materializedKeyOrError_MaterializedKey {
  __typename: "MaterializedKey";
  id: string;
  key: AssetEventsQuery_materializedKeyOrError_MaterializedKey_key;
  assetObservations: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetObservations[];
  assetMaterializations: AssetEventsQuery_materializedKeyOrError_MaterializedKey_assetMaterializations[];
  definition: AssetEventsQuery_materializedKeyOrError_MaterializedKey_definition | null;
}

export type AssetEventsQuery_materializedKeyOrError = AssetEventsQuery_materializedKeyOrError_AssetNotFoundError | AssetEventsQuery_materializedKeyOrError_MaterializedKey;

export interface AssetEventsQuery {
  materializedKeyOrError: AssetEventsQuery_materializedKeyOrError;
}

export interface AssetEventsQueryVariables {
  assetKey: AssetKeyInput;
  limit?: number | null;
  before?: string | null;
  partitionInLast?: number | null;
}
