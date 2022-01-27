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

export interface AssetMaterializationFragment_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
}

export interface AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface AssetMaterializationFragment_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetMaterializationFragment_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetMaterializationFragment_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetMaterializationFragment_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetMaterializationFragment_metadataEntries_EventAssetMetadataEntry_assetKey;
}

<<<<<<< HEAD
export type AssetMaterializationFragment_metadataEntries = AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry | AssetMaterializationFragment_metadataEntries_EventPathMetadataEntry | AssetMaterializationFragment_metadataEntries_EventJsonMetadataEntry | AssetMaterializationFragment_metadataEntries_EventUrlMetadataEntry | AssetMaterializationFragment_metadataEntries_EventTextMetadataEntry | AssetMaterializationFragment_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationFragment_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationFragment_metadataEntries_EventFloatMetadataEntry | AssetMaterializationFragment_metadataEntries_EventIntMetadataEntry | AssetMaterializationFragment_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationFragment_metadataEntries_EventAssetMetadataEntry;
=======
<<<<<<< HEAD
export type AssetMaterializationFragment_metadataEntries = AssetMaterializationFragment_metadataEntries_EventPathMetadataEntry | AssetMaterializationFragment_metadataEntries_EventJsonMetadataEntry | AssetMaterializationFragment_metadataEntries_EventUrlMetadataEntry | AssetMaterializationFragment_metadataEntries_EventTextMetadataEntry | AssetMaterializationFragment_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationFragment_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationFragment_metadataEntries_EventFloatMetadataEntry | AssetMaterializationFragment_metadataEntries_EventIntMetadataEntry | AssetMaterializationFragment_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationFragment_metadataEntries_EventAssetMetadataEntry;
=======
export interface AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetMaterializationFragment_metadataEntries = AssetMaterializationFragment_metadataEntries_EventPathMetadataEntry | AssetMaterializationFragment_metadataEntries_EventJsonMetadataEntry | AssetMaterializationFragment_metadataEntries_EventUrlMetadataEntry | AssetMaterializationFragment_metadataEntries_EventTextMetadataEntry | AssetMaterializationFragment_metadataEntries_EventMarkdownMetadataEntry | AssetMaterializationFragment_metadataEntries_EventPythonArtifactMetadataEntry | AssetMaterializationFragment_metadataEntries_EventFloatMetadataEntry | AssetMaterializationFragment_metadataEntries_EventIntMetadataEntry | AssetMaterializationFragment_metadataEntries_EventPipelineRunMetadataEntry | AssetMaterializationFragment_metadataEntries_EventAssetMetadataEntry | AssetMaterializationFragment_metadataEntries_EventTableMetadataEntry | AssetMaterializationFragment_metadataEntries_EventTableSchemaMetadataEntry;
>>>>>>> 54b3ea81e ([dagit-type-metadata] update graphql types)
>>>>>>> 3bea9c582 ([dagit-type-metadata] update graphql types)

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
  stepStats: AssetMaterializationFragment_stepStats;
  label: string;
  description: string | null;
  metadataEntries: AssetMaterializationFragment_metadataEntries[];
  assetLineage: AssetMaterializationFragment_assetLineage[];
}
