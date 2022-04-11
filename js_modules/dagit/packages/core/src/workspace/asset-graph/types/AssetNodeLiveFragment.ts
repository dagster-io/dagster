/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetNodeLiveFragment
// ====================================================

export interface AssetNodeLiveFragment_repository_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface AssetNodeLiveFragment_repository {
  __typename: "Repository";
  id: string;
  name: string;
  location: AssetNodeLiveFragment_repository_location;
}

export interface AssetNodeLiveFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetNodeLiveFragment_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  pipelineName: string;
  pipelineSnapshotId: string | null;
  repositoryOrigin: AssetNodeLiveFragment_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
}

export type AssetNodeLiveFragment_assetMaterializations_runOrError = AssetNodeLiveFragment_assetMaterializations_runOrError_RunNotFoundError | AssetNodeLiveFragment_assetMaterializations_runOrError_Run;

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeLiveFragment_assetMaterializations_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table_schema;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry_table;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type AssetNodeLiveFragment_assetMaterializations_metadataEntries = AssetNodeLiveFragment_assetMaterializations_metadataEntries_PathMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_JsonMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_UrlMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_TextMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_MarkdownMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_PythonArtifactMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_FloatMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_IntMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_PipelineRunMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_AssetMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_TableSchemaMetadataEntry;

export interface AssetNodeLiveFragment_assetMaterializations_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetNodeLiveFragment_assetMaterializations_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
}

export interface AssetNodeLiveFragment_assetMaterializations {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetNodeLiveFragment_assetMaterializations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  metadataEntries: AssetNodeLiveFragment_assetMaterializations_metadataEntries[];
  assetLineage: AssetNodeLiveFragment_assetMaterializations_assetLineage[];
  stepStats: AssetNodeLiveFragment_assetMaterializations_stepStats;
}

export interface AssetNodeLiveFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  repository: AssetNodeLiveFragment_repository;
  assetKey: AssetNodeLiveFragment_assetKey;
  assetMaterializations: AssetNodeLiveFragment_assetMaterializations[];
}
