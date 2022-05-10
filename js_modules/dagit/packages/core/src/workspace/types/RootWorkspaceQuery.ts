/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RepositoryLocationLoadStatus, InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RootWorkspaceQuery
// ====================================================

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes {
  __typename: "Mode";
  id: string;
  name: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry_table;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_PathMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_JsonMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_UrlMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TextMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_MarkdownMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_PythonArtifactMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_FloatMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_IntMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_PipelineRunMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_AssetMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableMetadataEntry | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries_TableSchemaMetadataEntry;

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_jobTags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines {
  __typename: "Pipeline";
  id: string;
  name: string;
  isJob: boolean;
  graphName: string;
  pipelineSnapshotId: string;
  modes: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_modes[];
  metadataEntries: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_metadataEntries[];
  jobTags: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines_jobTags[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  pipelineName: string;
  scheduleState: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules_scheduleState;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets {
  __typename: "Target";
  mode: string;
  pipelineName: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_targets[] | null;
  sensorState: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors_sensorState;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets {
  __typename: "PartitionSet";
  id: string;
  mode: string;
  pipelineName: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location {
  __typename: "RepositoryLocation";
  id: string;
  name: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata {
  __typename: "RepositoryMetadata";
  key: string;
  value: string;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories {
  __typename: "Repository";
  id: string;
  name: string;
  pipelines: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_pipelines[];
  schedules: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_schedules[];
  sensors: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_sensors[];
  partitionSets: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_partitionSets[];
  location: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_location;
  displayMetadata: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories_displayMetadata[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation {
  __typename: "RepositoryLocation";
  id: string;
  isReloadSupported: boolean;
  serverId: string | null;
  name: string;
  repositories: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation_repositories[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError_cause | null;
}

export type RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError = RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_RepositoryLocation | RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError_PythonError;

export interface RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries {
  __typename: "WorkspaceLocationEntry";
  id: string;
  name: string;
  loadStatus: RepositoryLocationLoadStatus;
  displayMetadata: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_displayMetadata[];
  updatedTimestamp: number;
  locationOrLoadError: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries_locationOrLoadError | null;
}

export interface RootWorkspaceQuery_workspaceOrError_Workspace {
  __typename: "Workspace";
  locationEntries: RootWorkspaceQuery_workspaceOrError_Workspace_locationEntries[];
}

export interface RootWorkspaceQuery_workspaceOrError_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RootWorkspaceQuery_workspaceOrError_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RootWorkspaceQuery_workspaceOrError_PythonError_cause | null;
}

export type RootWorkspaceQuery_workspaceOrError = RootWorkspaceQuery_workspaceOrError_Workspace | RootWorkspaceQuery_workspaceOrError_PythonError;

export interface RootWorkspaceQuery {
  workspaceOrError: RootWorkspaceQuery_workspaceOrError;
}
