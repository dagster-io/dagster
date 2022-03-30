/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { PipelineSelector } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetGraphQuery
// ====================================================

export interface AssetGraphQuery_assetNodes_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetGraphQuery_assetNodes_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry_table;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetGraphQuery_assetNodes_metadataEntries = AssetGraphQuery_assetNodes_metadataEntries_PathMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_JsonMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_UrlMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_TextMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_MarkdownMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_PythonArtifactMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_FloatMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_IntMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_PipelineRunMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_AssetMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_TableMetadataEntry | AssetGraphQuery_assetNodes_metadataEntries_TableSchemaMetadataEntry;

export interface AssetGraphQuery_assetNodes_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetGraphQuery_assetNodes_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetGraphQuery_assetNodes_repository_location;
}

export interface AssetGraphQuery_assetNodes_dependencyKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes_dependedByKeys {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetGraphQuery_assetNodes {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  description: string | null;
  metadataEntries: AssetGraphQuery_assetNodes_metadataEntries[];
  partitionDefinition: string | null;
  assetKey: AssetGraphQuery_assetNodes_assetKey;
  repository: AssetGraphQuery_assetNodes_repository;
  jobNames: string[];
  dependencyKeys: AssetGraphQuery_assetNodes_dependencyKeys[];
  dependedByKeys: AssetGraphQuery_assetNodes_dependedByKeys[];
}

export interface AssetGraphQuery {
  assetNodes: AssetGraphQuery_assetNodes[];
}

export interface AssetGraphQueryVariables {
  pipelineSelector?: PipelineSelector | null;
}
