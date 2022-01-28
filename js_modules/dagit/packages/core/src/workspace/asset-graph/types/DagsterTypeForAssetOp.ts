/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositorySelector } from "./../../../types/globalTypes";

// ====================================================
// GraphQL query operation: DagsterTypeForAssetOp
// ====================================================

export interface DagsterTypeForAssetOp_repositoryOrError_PythonError {
  __typename: "PythonError" | "RepositoryNotFoundError";
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry_table;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries = DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPathMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventJsonMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventUrlMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTextMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventMarkdownMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPythonArtifactMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventFloatMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventIntMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventPipelineRunMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventAssetMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableMetadataEntry | DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries_EventTableSchemaMetadataEntry;

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type {
  __typename: "RegularDagsterType" | "ListDagsterType" | "NullableDagsterType";
  name: string | null;
  description: string | null;
  metadataEntries: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type_metadataEntries[];
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions {
  __typename: "OutputDefinition";
  type: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions_type;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition {
  __typename: "SolidDefinition" | "CompositeSolidDefinition";
  outputDefinitions: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition_outputDefinitions[];
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid {
  __typename: "UsedSolid";
  definition: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid_definition;
}

export interface DagsterTypeForAssetOp_repositoryOrError_Repository {
  __typename: "Repository";
  id: string;
  usedSolid: DagsterTypeForAssetOp_repositoryOrError_Repository_usedSolid | null;
}

export type DagsterTypeForAssetOp_repositoryOrError = DagsterTypeForAssetOp_repositoryOrError_PythonError | DagsterTypeForAssetOp_repositoryOrError_Repository;

export interface DagsterTypeForAssetOp {
  repositoryOrError: DagsterTypeForAssetOp_repositoryOrError;
}

export interface DagsterTypeForAssetOpVariables {
  repoSelector: RepositorySelector;
  assetOpName: string;
}
