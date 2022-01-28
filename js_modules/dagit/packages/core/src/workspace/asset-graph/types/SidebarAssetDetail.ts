/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: SidebarAssetDetail
// ====================================================

export interface SidebarAssetDetail_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries = SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPathMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTextMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventIntMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry | SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry;

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  description: string | null;
  metadataEntries: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries[];
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions {
  __typename: "OutputDefinition";
  type: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type;
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  outputDefinitions: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition_outputDefinitions[];
}

export interface SidebarAssetDetail_repositoryOrError_Repository_usedSolid {
  __typename: "UsedSolid";
  definition: SidebarAssetDetail_repositoryOrError_Repository_usedSolid_definition;
}

export interface SidebarAssetDetail_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolid: SidebarAssetDetail_repositoryOrError_Repository_usedSolid | null;
}

export type SidebarAssetDetail_repositoryOrError = SidebarAssetDetail_repositoryOrError_PythonError | SidebarAssetDetail_repositoryOrError_Repository;

export interface SidebarAssetDetail {
  repositoryOrError: SidebarAssetDetail_repositoryOrError;
}

export interface SidebarAssetDetailVariables {
  repoSelector: RepositorySelector;
  opName: string;
}
