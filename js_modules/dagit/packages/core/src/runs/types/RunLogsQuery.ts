/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, LogLevel, DagsterEventType, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: RunLogsQuery
// ====================================================

export interface RunLogsQuery_pipelineRunOrError_RunNotFoundError {
  __typename: "RunNotFoundError" | "PythonError";
}

export interface RunLogsQuery_pipelineRunOrError_Run {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  canTerminate: boolean;
}

export type RunLogsQuery_pipelineRunOrError = RunLogsQuery_pipelineRunOrError_RunNotFoundError | RunLogsQuery_pipelineRunOrError_Run;

export interface RunLogsQuery_logsForRun_RunNotFoundError {
  __typename: "RunNotFoundError";
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent" | "AlertFailureEvent" | "AssetMaterializationPlannedEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent {
  __typename: "MaterializationEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent {
  __typename: "ObservationEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_RunFailureEvent_pipelineFailureError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_RunFailureEvent_pipelineFailureError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_logsForRun_EventConnection_events_RunFailureEvent_pipelineFailureError_cause | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_RunFailureEvent {
  __typename: "RunFailureEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  pipelineFailureError: RunLogsQuery_logsForRun_EventConnection_events_RunFailureEvent_pipelineFailureError | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_error_cause | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_error | null;
  errorSource: ErrorSource | null;
  failureMetadata: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepUpForRetryEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepUpForRetryEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepUpForRetryEvent_error_cause | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepUpForRetryEvent {
  __typename: "ExecutionStepUpForRetryEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepUpForRetryEvent_error | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  inputName: string;
  typeCheck: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent_typeCheck;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  typeCheck: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_typeCheck;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  expectationResult: RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent_expectationResult;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  operationResult: RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent_operationResult;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  managerKey: string;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent {
  __typename: "LoadedInputEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  inputName: string;
  managerKey: string;
  upstreamOutputName: string | null;
  upstreamStepKey: string | null;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent_metadataEntries[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries = RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_PathMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_JsonMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_UrlMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TextMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_MarkdownMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_PythonArtifactMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_FloatMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_IntMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_BoolMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_PipelineRunMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_AssetMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableMetadataEntry | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_engineError_cause | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_EngineEvent {
  __typename: "EngineEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  metadataEntries: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_metadataEntries[];
  engineError: RunLogsQuery_logsForRun_EventConnection_events_EngineEvent_engineError | null;
  markerStart: string | null;
  markerEnd: string | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HookErroredEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HookErroredEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunLogsQuery_logsForRun_EventConnection_events_HookErroredEvent_error_cause | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_HookErroredEvent {
  __typename: "HookErroredEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunLogsQuery_logsForRun_EventConnection_events_HookErroredEvent_error | null;
}

export interface RunLogsQuery_logsForRun_EventConnection_events_LogsCapturedEvent {
  __typename: "LogsCapturedEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  logKey: string;
  stepKeys: string[] | null;
  pid: number | null;
}

export type RunLogsQuery_logsForRun_EventConnection_events = RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepSkippedEvent | RunLogsQuery_logsForRun_EventConnection_events_MaterializationEvent | RunLogsQuery_logsForRun_EventConnection_events_ObservationEvent | RunLogsQuery_logsForRun_EventConnection_events_RunFailureEvent | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepFailureEvent | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepUpForRetryEvent | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepInputEvent | RunLogsQuery_logsForRun_EventConnection_events_ExecutionStepOutputEvent | RunLogsQuery_logsForRun_EventConnection_events_StepExpectationResultEvent | RunLogsQuery_logsForRun_EventConnection_events_ObjectStoreOperationEvent | RunLogsQuery_logsForRun_EventConnection_events_HandledOutputEvent | RunLogsQuery_logsForRun_EventConnection_events_LoadedInputEvent | RunLogsQuery_logsForRun_EventConnection_events_EngineEvent | RunLogsQuery_logsForRun_EventConnection_events_HookErroredEvent | RunLogsQuery_logsForRun_EventConnection_events_LogsCapturedEvent;

export interface RunLogsQuery_logsForRun_EventConnection {
  __typename: "EventConnection";
  events: RunLogsQuery_logsForRun_EventConnection_events[];
  cursor: string;
}

export interface RunLogsQuery_logsForRun_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type RunLogsQuery_logsForRun = RunLogsQuery_logsForRun_RunNotFoundError | RunLogsQuery_logsForRun_EventConnection | RunLogsQuery_logsForRun_PythonError;

export interface RunLogsQuery {
  pipelineRunOrError: RunLogsQuery_pipelineRunOrError;
  logsForRun: RunLogsQuery_logsForRun;
}

export interface RunLogsQueryVariables {
  runId: string;
  cursor?: string | null;
  limit?: number | null;
}
