/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DagsterEventType, LogLevel, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsRowStructuredFragment
// ====================================================

export interface LogsRowStructuredFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent" | "AlertFailureEvent" | "AssetMaterializationPlannedEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries = LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string | null;
  description: string | null;
  success: boolean;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries[];
  outputName: string;
  typeCheck: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries = LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_ResourceInitFailureEvent_error_cause | null;
}

export interface LogsRowStructuredFragment_ResourceInitFailureEvent {
  __typename: "ResourceInitFailureEvent" | "EngineEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_ResourceInitFailureEvent_metadataEntries[];
  markerStart: string | null;
  markerEnd: string | null;
  error: LogsRowStructuredFragment_ResourceInitFailureEvent_error | null;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries = LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ResourceInitStartedEvent {
  __typename: "ResourceInitStartedEvent" | "ResourceInitSuccessEvent" | "StepWorkerStartedEvent" | "StepWorkerStartingEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_ResourceInitStartedEvent_metadataEntries[];
  markerStart: string | null;
  markerEnd: string | null;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_HandledOutputEvent_metadataEntries = LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries[];
  outputName: string;
  managerKey: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_LoadedInputEvent_metadataEntries = LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_LoadedInputEvent {
  __typename: "LoadedInputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_LoadedInputEvent_metadataEntries[];
  inputName: string;
  managerKey: string;
  upstreamOutputName: string | null;
  upstreamStepKey: string | null;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_MaterializationEvent_metadataEntries = LogsRowStructuredFragment_MaterializationEvent_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_MaterializationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent {
  __typename: "MaterializationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_MaterializationEvent_metadataEntries[];
  assetKey: LogsRowStructuredFragment_MaterializationEvent_assetKey | null;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ObservationEvent_metadataEntries = LogsRowStructuredFragment_ObservationEvent_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ObservationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ObservationEvent {
  __typename: "ObservationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_ObservationEvent_metadataEntries[];
  assetKey: LogsRowStructuredFragment_ObservationEvent_assetKey | null;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_ExecutionStepFailureEvent_error_cause | null;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsRowStructuredFragment_ExecutionStepFailureEvent_error | null;
  errorSource: ErrorSource | null;
  failureMetadata: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface LogsRowStructuredFragment_ExecutionStepUpForRetryEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepUpForRetryEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_ExecutionStepUpForRetryEvent_error_cause | null;
}

export interface LogsRowStructuredFragment_ExecutionStepUpForRetryEvent {
  __typename: "ExecutionStepUpForRetryEvent" | "RunFailureEvent" | "HookErroredEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsRowStructuredFragment_ExecutionStepUpForRetryEvent_error | null;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string | null;
  description: string | null;
  success: boolean;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  inputName: string;
  typeCheck: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries = LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string | null;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  expectationResult: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry;

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  operationResult: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult;
}

export interface LogsRowStructuredFragment_LogsCapturedEvent {
  __typename: "LogsCapturedEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  logKey: string;
  stepKeys: string[] | null;
}

export type LogsRowStructuredFragment = LogsRowStructuredFragment_ExecutionStepSkippedEvent | LogsRowStructuredFragment_ExecutionStepOutputEvent | LogsRowStructuredFragment_ResourceInitFailureEvent | LogsRowStructuredFragment_ResourceInitStartedEvent | LogsRowStructuredFragment_HandledOutputEvent | LogsRowStructuredFragment_LoadedInputEvent | LogsRowStructuredFragment_MaterializationEvent | LogsRowStructuredFragment_ObservationEvent | LogsRowStructuredFragment_ExecutionStepFailureEvent | LogsRowStructuredFragment_ExecutionStepUpForRetryEvent | LogsRowStructuredFragment_ExecutionStepInputEvent | LogsRowStructuredFragment_StepExpectationResultEvent | LogsRowStructuredFragment_ObjectStoreOperationEvent | LogsRowStructuredFragment_LogsCapturedEvent;
