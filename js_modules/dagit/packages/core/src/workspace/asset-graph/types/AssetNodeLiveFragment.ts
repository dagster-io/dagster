/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../../types/globalTypes";

// ====================================================
// GraphQL fragment: AssetNodeLiveFragment
// ====================================================

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

export interface AssetNodeLiveFragment_assetMaterializations_stepStats {
  __typename: "RunStepStats";
  endTime: number | null;
  startTime: number | null;
  stepKey: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry" | "EventTableMetadataEntry";
  label: string;
  description: string | null;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventAssetMetadataEntry_assetKey;
}

<<<<<<< HEAD
export type AssetNodeLiveFragment_assetMaterializations_metadataEntries = AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPathMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventJsonMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventUrlMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTextMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventFloatMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventIntMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventAssetMetadataEntry;
=======
<<<<<<< HEAD
export type AssetNodeLiveFragment_assetMaterializations_metadataEntries = AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPathMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventJsonMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventUrlMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTextMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventFloatMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventIntMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventAssetMetadataEntry;
=======
export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns_constraints;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_columns[];
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema_constraints | null;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table_schema;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry {
  __typename: "EventTableMetadataEntry";
  label: string;
  description: string | null;
  table: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry_table;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns_constraints;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_columns[];
  constraints: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema_constraints | null;
}

export interface AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry {
  __typename: "EventTableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry_schema;
}

export type AssetNodeLiveFragment_assetMaterializations_metadataEntries = AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPathMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventJsonMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventUrlMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTextMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventMarkdownMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPythonArtifactMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventFloatMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventIntMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventPipelineRunMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventAssetMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableMetadataEntry | AssetNodeLiveFragment_assetMaterializations_metadataEntries_EventTableSchemaMetadataEntry;
>>>>>>> 54b3ea81e ([dagit-type-metadata] update graphql types)
>>>>>>> 3bea9c582 ([dagit-type-metadata] update graphql types)

export interface AssetNodeLiveFragment_assetMaterializations_assetLineage_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations_assetLineage {
  __typename: "AssetLineageInfo";
  assetKey: AssetNodeLiveFragment_assetMaterializations_assetLineage_assetKey;
  partitions: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations {
  __typename: "MaterializationEvent";
  partition: string | null;
  runOrError: AssetNodeLiveFragment_assetMaterializations_runOrError;
  runId: string;
  timestamp: string;
  stepKey: string | null;
  stepStats: AssetNodeLiveFragment_assetMaterializations_stepStats;
  metadataEntries: AssetNodeLiveFragment_assetMaterializations_metadataEntries[];
  assetLineage: AssetNodeLiveFragment_assetMaterializations_assetLineage[];
}

export interface AssetNodeLiveFragment {
  __typename: "AssetNode";
  id: string;
  opName: string | null;
  assetMaterializations: AssetNodeLiveFragment_assetMaterializations[];
}
