/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunMetadataProviderMessageFragment
// ====================================================

export interface RunMetadataProviderMessageFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent" | "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunFailureEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "HandledOutputEvent" | "LoadedInputEvent" | "StepExpectationResultEvent" | "MaterializationEvent" | "ObservationEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "HookErroredEvent" | "AlertStartEvent" | "AlertSuccessEvent" | "AlertFailureEvent" | "AssetMaterializationPlannedEvent";
  message: string;
  timestamp: string;
  stepKey: string | null;
}

export interface RunMetadataProviderMessageFragment_ResourceInitFailureEvent {
  __typename: "ResourceInitFailureEvent" | "ResourceInitStartedEvent" | "ResourceInitSuccessEvent" | "StepWorkerStartedEvent" | "StepWorkerStartingEvent" | "EngineEvent";
  message: string;
  timestamp: string;
  stepKey: string | null;
  markerStart: string | null;
  markerEnd: string | null;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry {
  __typename: "PathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry {
  __typename: "JsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry {
  __typename: "UrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry {
  __typename: "TextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry {
  __typename: "MarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry {
  __typename: "PythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry {
  __typename: "FloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry {
  __typename: "IntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry {
  __typename: "BoolMetadataEntry";
  label: string;
  description: string | null;
  boolValue: boolean | null;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry {
  __typename: "PipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry {
  __typename: "AssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry_assetKey;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns_constraints;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema {
  __typename: "TableSchema";
  columns: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_columns[];
  constraints: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema_constraints | null;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table {
  __typename: "Table";
  records: string[];
  schema: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table_schema;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry {
  __typename: "TableMetadataEntry";
  label: string;
  description: string | null;
  table: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry_table;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints {
  __typename: "TableColumnConstraints";
  nullable: boolean;
  unique: boolean;
  other: string[];
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns {
  __typename: "TableColumn";
  name: string;
  description: string | null;
  type: string;
  constraints: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns_constraints;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints {
  __typename: "TableConstraints";
  other: string[];
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema {
  __typename: "TableSchema";
  columns: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_columns[];
  constraints: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema_constraints | null;
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry {
  __typename: "TableSchemaMetadataEntry";
  label: string;
  description: string | null;
  schema: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry_schema;
}

export type RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PathMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_JsonMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_UrlMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TextMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_MarkdownMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PythonArtifactMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_FloatMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_IntMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_BoolMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_PipelineRunMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_AssetMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableMetadataEntry | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_TableSchemaMetadataEntry;

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunMetadataProviderMessageFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  stepKey: string | null;
  operationResult: RunMetadataProviderMessageFragment_ObjectStoreOperationEvent_operationResult;
}

export interface RunMetadataProviderMessageFragment_LogsCapturedEvent {
  __typename: "LogsCapturedEvent";
  message: string;
  timestamp: string;
  stepKey: string | null;
  logKey: string;
  stepKeys: string[] | null;
  pid: number | null;
}

export type RunMetadataProviderMessageFragment = RunMetadataProviderMessageFragment_ExecutionStepFailureEvent | RunMetadataProviderMessageFragment_ResourceInitFailureEvent | RunMetadataProviderMessageFragment_ObjectStoreOperationEvent | RunMetadataProviderMessageFragment_LogsCapturedEvent;
