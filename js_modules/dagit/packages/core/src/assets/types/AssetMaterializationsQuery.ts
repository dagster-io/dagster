/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: AssetMaterializationsQuery
// ====================================================

export interface AssetMaterializationsQuery_assetOrError_AssetNotFoundError {
  __typename: "AssetNotFoundError";
}

export interface AssetMaterializationsQuery_assetOrError_Asset_key {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  mode: string;
  repositoryOrigin: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run_repositoryOrigin | null;
  status: RunStatus;
  pipelineName: string;
  pipelineSnapshotId: string | null;
}

export type AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError = AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_RunNotFoundError | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError_Run;

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventAssetMetadataEntry_assetKey;
}

<<<<<<< HEAD
export type AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries = AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPathMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventJsonMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventUrlMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTextMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventFloatMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventIntMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventAssetMetadataEntry;
=======
<<<<<<< HEAD
export type AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries = AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPathMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventJsonMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventUrlMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTextMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventFloatMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventIntMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventAssetMetadataEntry;
=======
export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries = AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPathMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventJsonMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventUrlMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTextMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventFloatMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventIntMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventAssetMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableMetadataEntry | AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry;
>>>>>>> 54b3ea81e ([dagit-type-metadata] update graphql types)
>>>>>>> 3bea9c582 ([dagit-type-metadata] update graphql types)

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_stepStats;
  label: string;
  description: string | null;
  metadataEntries: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_metadataEntries[];
  assetLineage: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations_assetLineage[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset_definition {
  __typename: "AssetNode";
  id: string;
  partitionKeys: string[];
}

export interface AssetMaterializationsQuery_assetOrError_Asset {
  __typename: "Asset";
  id: string;
  key: AssetMaterializationsQuery_assetOrError_Asset_key;
  assetMaterializations: AssetMaterializationsQuery_assetOrError_Asset_assetMaterializations[];
  definition: AssetMaterializationsQuery_assetOrError_Asset_definition | null;
}

export type AssetMaterializationsQuery_assetOrError = AssetMaterializationsQuery_assetOrError_AssetNotFoundError | AssetMaterializationsQuery_assetOrError_Asset;

export interface AssetMaterializationsQuery {
  assetOrError: AssetMaterializationsQuery_assetOrError;
}

export interface AssetMaterializationsQueryVariables {
  assetKey: AssetKeyInput;
  limit?: number | null;
  before?: string | null;
  partitionInLast?: number | null;
}
