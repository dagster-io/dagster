/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetPartitionDetailQuery
// ====================================================

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError = AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError_RunNotFoundError | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError_Run;

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_NotebookMetadataEntry {
  __typename: "NotebookMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry_table;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries = AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_PathMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_NotebookMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_JsonMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_UrlMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TextMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_MarkdownMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_FloatMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_IntMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_BoolMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_PipelineRunMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_AssetMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableMetadataEntry | AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries_TableSchemaMetadataEntry;

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations {
  __typename: "MaterializationEvent";
  runId: string;
  partition: string | null;
  runOrError: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_runOrError;
  timestamp: string;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_metadataEntries[];
  assetLineage: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations_assetLineage[];
}

export interface AssetPartitionDetailQuery_assetNodeOrError_AssetNode {
  __typename: "AssetNode";
  id: string;
  assetMaterializations: AssetPartitionDetailQuery_assetNodeOrError_AssetNode_assetMaterializations[];
}

export type AssetPartitionDetailQuery_assetNodeOrError = AssetPartitionDetailQuery_assetNodeOrError_AssetNotFoundError | AssetPartitionDetailQuery_assetNodeOrError_AssetNode;

export interface AssetPartitionDetailQuery {
  assetNodeOrError: AssetPartitionDetailQuery_assetNodeOrError;
}

export interface AssetPartitionDetailQueryVariables {
  assetKey: AssetKeyInput;
  partitionKey: string;
}
