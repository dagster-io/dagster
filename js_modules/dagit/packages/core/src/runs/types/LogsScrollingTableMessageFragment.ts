// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DagsterEventType, LogLevel, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsScrollingTableMessageFragment
// ====================================================

export interface LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries = LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventAssetMetadataEntry;

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  assetKey: LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  materialization: LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization;
}

export interface LogsScrollingTableMessageFragment_RunFailureEvent_pipelineFailureError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_RunFailureEvent_pipelineFailureError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsScrollingTableMessageFragment_RunFailureEvent_pipelineFailureError_cause | null;
}

export interface LogsScrollingTableMessageFragment_RunFailureEvent {
  __typename: "RunFailureEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  pipelineFailureError: LogsScrollingTableMessageFragment_RunFailureEvent_pipelineFailureError | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error_cause | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry;

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

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
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

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  outputName: string;
  typeCheck: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck;
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries = LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry;

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
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

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry;

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

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries = LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface LogsScrollingTableMessageFragment_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  outputName: string;
  managerKey: string;
  metadataEntries: LogsScrollingTableMessageFragment_HandledOutputEvent_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_LoadedInputEvent {
  __typename: "LoadedInputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  inputName: string;
  managerKey: string;
  upstreamOutputName: string | null;
  upstreamStepKey: string | null;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsScrollingTableMessageFragment_EngineEvent_metadataEntries = LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventIntMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry;

export interface LogsScrollingTableMessageFragment_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsScrollingTableMessageFragment_EngineEvent_engineError_cause | null;
}

export interface LogsScrollingTableMessageFragment_EngineEvent {
  __typename: "EngineEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_EngineEvent_metadataEntries[];
  engineError: LogsScrollingTableMessageFragment_EngineEvent_engineError | null;
}

export interface LogsScrollingTableMessageFragment_HookErroredEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_HookErroredEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsScrollingTableMessageFragment_HookErroredEvent_error_cause | null;
}

export interface LogsScrollingTableMessageFragment_HookErroredEvent {
  __typename: "HookErroredEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsScrollingTableMessageFragment_HookErroredEvent_error | null;
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

export type LogsScrollingTableMessageFragment = LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent | LogsScrollingTableMessageFragment_StepMaterializationEvent | LogsScrollingTableMessageFragment_RunFailureEvent | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent | LogsScrollingTableMessageFragment_ExecutionStepInputEvent | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent | LogsScrollingTableMessageFragment_StepExpectationResultEvent | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent | LogsScrollingTableMessageFragment_HandledOutputEvent | LogsScrollingTableMessageFragment_LoadedInputEvent | LogsScrollingTableMessageFragment_EngineEvent | LogsScrollingTableMessageFragment_HookErroredEvent | LogsScrollingTableMessageFragment_LogsCapturedEvent;
