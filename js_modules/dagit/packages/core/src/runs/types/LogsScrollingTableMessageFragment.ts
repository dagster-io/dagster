/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DagsterEventType, LogLevel, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsScrollingTableMessageFragment
// ====================================================

export interface LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent" | "AlertFailureEvent" | "AssetMaterializationPlannedEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string | null;
  description: string | null;
  success: boolean;
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries[];
  outputName: string;
  typeCheck: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries = LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_error_causes[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitFailureEvent {
  __typename: "ResourceInitFailureEvent" | "EngineEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_metadataEntries[];
  markerStart: string | null;
  markerEnd: string | null;
  error: LogsScrollingTableMessageFragment_ResourceInitFailureEvent_error | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries = LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ResourceInitStartedEvent {
  __typename: "ResourceInitStartedEvent" | "ResourceInitSuccessEvent" | "StepWorkerStartedEvent" | "StepWorkerStartingEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_ResourceInitStartedEvent_metadataEntries[];
  markerStart: string | null;
  markerEnd: string | null;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries = LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries[];
  outputName: string;
  managerKey: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries = LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_LoadedInputEvent {
  __typename: "LoadedInputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_LoadedInputEvent_metadataEntries[];
  inputName: string;
  managerKey: string;
  upstreamOutputName: string | null;
  upstreamStepKey: string | null;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries = LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_MaterializationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_MaterializationEvent {
  __typename: "MaterializationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_MaterializationEvent_metadataEntries[];
  assetKey: LogsScrollingTableMessageFragment_MaterializationEvent_assetKey | null;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries = LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ObservationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ObservationEvent {
  __typename: "ObservationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_ObservationEvent_metadataEntries[];
  assetKey: LogsScrollingTableMessageFragment_ObservationEvent_assetKey | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error_causes[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error | null;
  errorSource: ErrorSource | null;
  failureMetadata: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepUpForRetryEvent_error_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepUpForRetryEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: LogsScrollingTableMessageFragment_ExecutionStepUpForRetryEvent_error_causes[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepUpForRetryEvent {
  __typename: "ExecutionStepUpForRetryEvent" | "RunFailureEvent" | "HookErroredEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsScrollingTableMessageFragment_ExecutionStepUpForRetryEvent_error | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string | null;
  description: string | null;
  success: boolean;
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  inputName: string;
  typeCheck: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries = LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string | null;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  expectationResult: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry;

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  operationResult: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult;
}

export interface LogsScrollingTableMessageFragment_LogsCapturedEvent {
  __typename: "LogsCapturedEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  logKey: string;
  stepKeys: string[] | null;
}

export type LogsScrollingTableMessageFragment = LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent | LogsScrollingTableMessageFragment_ResourceInitFailureEvent | LogsScrollingTableMessageFragment_ResourceInitStartedEvent | LogsScrollingTableMessageFragment_HandledOutputEvent | LogsScrollingTableMessageFragment_LoadedInputEvent | LogsScrollingTableMessageFragment_MaterializationEvent | LogsScrollingTableMessageFragment_ObservationEvent | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent | LogsScrollingTableMessageFragment_ExecutionStepUpForRetryEvent | LogsScrollingTableMessageFragment_ExecutionStepInputEvent | LogsScrollingTableMessageFragment_StepExpectationResultEvent | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent | LogsScrollingTableMessageFragment_LogsCapturedEvent;
