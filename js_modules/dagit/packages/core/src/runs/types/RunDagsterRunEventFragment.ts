/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { LogLevel, DagsterEventType, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunDagsterRunEventFragment
// ====================================================

export interface RunDagsterRunEventFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent" | "AssetMaterializationPlannedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_MaterializationEvent_metadataEntries = RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_MaterializationEvent {
  __typename: "MaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  assetKey: RunDagsterRunEventFragment_MaterializationEvent_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: RunDagsterRunEventFragment_MaterializationEvent_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ObservationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_ObservationEvent_metadataEntries = RunDagsterRunEventFragment_ObservationEvent_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_ObservationEvent {
  __typename: "ObservationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  assetKey: RunDagsterRunEventFragment_ObservationEvent_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: RunDagsterRunEventFragment_ObservationEvent_metadataEntries[];
}

export interface RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError_cause | null;
}

export interface RunDagsterRunEventFragment_RunFailureEvent {
  __typename: "RunFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  pipelineFailureError: RunDagsterRunEventFragment_RunFailureEvent_pipelineFailureError | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_ExecutionStepFailureEvent_error_cause | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunDagsterRunEventFragment_ExecutionStepFailureEvent_error | null;
  errorSource: ErrorSource | null;
  failureMetadata: RunDagsterRunEventFragment_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  inputName: string;
  typeCheck: RunDagsterRunEventFragment_ExecutionStepInputEvent_typeCheck;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries = RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  typeCheck: RunDagsterRunEventFragment_ExecutionStepOutputEvent_typeCheck;
  metadataEntries: RunDagsterRunEventFragment_ExecutionStepOutputEvent_metadataEntries[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries = RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunDagsterRunEventFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  expectationResult: RunDagsterRunEventFragment_StepExpectationResultEvent_expectationResult;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunDagsterRunEventFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  operationResult: RunDagsterRunEventFragment_ObjectStoreOperationEvent_operationResult;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries = RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  outputName: string;
  managerKey: string;
  metadataEntries: RunDagsterRunEventFragment_HandledOutputEvent_metadataEntries[];
}

export interface RunDagsterRunEventFragment_LoadedInputEvent {
  __typename: "LoadedInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  inputName: string;
  managerKey: string;
  upstreamOutputName: string | null;
  upstreamStepKey: string | null;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunDagsterRunEventFragment_EngineEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry_table;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunDagsterRunEventFragment_EngineEvent_metadataEntries = RunDagsterRunEventFragment_EngineEvent_metadataEntries_PathMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_JsonMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_UrlMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_TextMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_MarkdownMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_PythonArtifactMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_FloatMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_IntMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_PipelineRunMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_AssetMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableMetadataEntry | RunDagsterRunEventFragment_EngineEvent_metadataEntries_TableSchemaMetadataEntry;

export interface RunDagsterRunEventFragment_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_EngineEvent_engineError_cause | null;
}

export interface RunDagsterRunEventFragment_EngineEvent {
  __typename: "EngineEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  metadataEntries: RunDagsterRunEventFragment_EngineEvent_metadataEntries[];
  engineError: RunDagsterRunEventFragment_EngineEvent_engineError | null;
  markerStart: string | null;
  markerEnd: string | null;
}

export interface RunDagsterRunEventFragment_HookErroredEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunDagsterRunEventFragment_HookErroredEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunDagsterRunEventFragment_HookErroredEvent_error_cause | null;
}

export interface RunDagsterRunEventFragment_HookErroredEvent {
  __typename: "HookErroredEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  error: RunDagsterRunEventFragment_HookErroredEvent_error | null;
}

export interface RunDagsterRunEventFragment_LogsCapturedEvent {
  __typename: "LogsCapturedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  eventType: DagsterEventType | null;
  logKey: string;
  stepKeys: string[] | null;
  pid: number | null;
}

export type RunDagsterRunEventFragment = RunDagsterRunEventFragment_ExecutionStepSkippedEvent | RunDagsterRunEventFragment_MaterializationEvent | RunDagsterRunEventFragment_ObservationEvent | RunDagsterRunEventFragment_RunFailureEvent | RunDagsterRunEventFragment_ExecutionStepFailureEvent | RunDagsterRunEventFragment_ExecutionStepInputEvent | RunDagsterRunEventFragment_ExecutionStepOutputEvent | RunDagsterRunEventFragment_StepExpectationResultEvent | RunDagsterRunEventFragment_ObjectStoreOperationEvent | RunDagsterRunEventFragment_HandledOutputEvent | RunDagsterRunEventFragment_LoadedInputEvent | RunDagsterRunEventFragment_EngineEvent | RunDagsterRunEventFragment_HookErroredEvent | RunDagsterRunEventFragment_LogsCapturedEvent;
