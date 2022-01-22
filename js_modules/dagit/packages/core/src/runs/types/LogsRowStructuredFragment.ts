/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DagsterEventType, LogLevel, ErrorSource, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsRowStructuredFragment
// ====================================================

export interface LogsRowStructuredFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "RunStartEvent" | "RunEnqueuedEvent" | "RunDequeuedEvent" | "RunStartingEvent" | "RunCancelingEvent" | "RunCanceledEvent" | "RunSuccessEvent" | "ObservationEvent" | "HookCompletedEvent" | "HookSkippedEvent" | "AlertStartEvent" | "AlertSuccessEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
}

export interface LogsRowStructuredFragment_MaterializationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_MaterializationEvent_metadataEntries = LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_MaterializationEvent_metadataEntries_EventAssetMetadataEntry;

export interface LogsRowStructuredFragment_MaterializationEvent {
  __typename: "MaterializationEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  assetKey: LogsRowStructuredFragment_MaterializationEvent_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_MaterializationEvent_metadataEntries[];
}

export interface LogsRowStructuredFragment_RunFailureEvent_pipelineFailureError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_RunFailureEvent_pipelineFailureError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_RunFailureEvent_pipelineFailureError_cause | null;
}

export interface LogsRowStructuredFragment_RunFailureEvent {
  __typename: "RunFailureEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  pipelineFailureError: LogsRowStructuredFragment_RunFailureEvent_pipelineFailureError | null;
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

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventAssetMetadataEntry;

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

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
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

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventAssetMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries = LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  outputName: string;
  typeCheck: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepOutputEvent_metadataEntries[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries = LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventAssetMetadataEntry;

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
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

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventAssetMetadataEntry;

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

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_HandledOutputEvent_metadataEntries = LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_HandledOutputEvent_metadataEntries_EventAssetMetadataEntry;

export interface LogsRowStructuredFragment_HandledOutputEvent {
  __typename: "HandledOutputEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  outputName: string;
  managerKey: string;
  metadataEntries: LogsRowStructuredFragment_HandledOutputEvent_metadataEntries[];
}

export interface LogsRowStructuredFragment_LoadedInputEvent {
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

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number | null;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number | null;
  intRepr: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry {
  __typename: "EventPipelineRunMetadataEntry";
  label: string;
  description: string | null;
  runId: string;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry {
  __typename: "EventAssetMetadataEntry";
  label: string;
  description: string | null;
  assetKey: LogsRowStructuredFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry_assetKey;
}

export type LogsRowStructuredFragment_EngineEvent_metadataEntries = LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventIntMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPipelineRunMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventAssetMetadataEntry;

export interface LogsRowStructuredFragment_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_EngineEvent_engineError_cause | null;
}

export interface LogsRowStructuredFragment_EngineEvent {
  __typename: "EngineEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  metadataEntries: LogsRowStructuredFragment_EngineEvent_metadataEntries[];
  engineError: LogsRowStructuredFragment_EngineEvent_engineError | null;
}

export interface LogsRowStructuredFragment_HookErroredEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_HookErroredEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_HookErroredEvent_error_cause | null;
}

export interface LogsRowStructuredFragment_HookErroredEvent {
  __typename: "HookErroredEvent";
  message: string;
  eventType: DagsterEventType | null;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsRowStructuredFragment_HookErroredEvent_error | null;
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

export type LogsRowStructuredFragment = LogsRowStructuredFragment_ExecutionStepSkippedEvent | LogsRowStructuredFragment_MaterializationEvent | LogsRowStructuredFragment_RunFailureEvent | LogsRowStructuredFragment_ExecutionStepFailureEvent | LogsRowStructuredFragment_ExecutionStepInputEvent | LogsRowStructuredFragment_ExecutionStepOutputEvent | LogsRowStructuredFragment_StepExpectationResultEvent | LogsRowStructuredFragment_ObjectStoreOperationEvent | LogsRowStructuredFragment_HandledOutputEvent | LogsRowStructuredFragment_LoadedInputEvent | LogsRowStructuredFragment_EngineEvent | LogsRowStructuredFragment_HookErroredEvent | LogsRowStructuredFragment_LogsCapturedEvent;
