// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsRowStructuredFragment
// ====================================================

export interface LogsRowStructuredFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  floatValue: number;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries = LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventIntMetadataEntry;

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  assetKey: LogsRowStructuredFragment_StepMaterializationEvent_materialization_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface LogsRowStructuredFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  materialization: LogsRowStructuredFragment_StepMaterializationEvent_materialization;
}

export interface LogsRowStructuredFragment_PipelineInitFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_PipelineInitFailureEvent_error_cause | null;
}

export interface LogsRowStructuredFragment_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsRowStructuredFragment_PipelineInitFailureEvent_error;
}

export interface LogsRowStructuredFragment_PipelineFailureEvent_pipelineFailureError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsRowStructuredFragment_PipelineFailureEvent_pipelineFailureError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsRowStructuredFragment_PipelineFailureEvent_pipelineFailureError_cause | null;
}

export interface LogsRowStructuredFragment_PipelineFailureEvent {
  __typename: "PipelineFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  pipelineFailureError: LogsRowStructuredFragment_PipelineFailureEvent_pipelineFailureError | null;
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
  floatValue: number;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventIntMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: LogsRowStructuredFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsRowStructuredFragment_ExecutionStepFailureEvent_error;
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
  floatValue: number;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventIntMetadataEntry;

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
  floatValue: number;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventIntMetadataEntry;

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  outputName: string;
  typeCheck: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck;
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
  floatValue: number;
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries = LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventIntMetadataEntry;

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
  floatValue: number;
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventIntMetadataEntry;

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface LogsRowStructuredFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  operationResult: LogsRowStructuredFragment_ObjectStoreOperationEvent_operationResult;
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
  floatValue: number;
}

export interface LogsRowStructuredFragment_EngineEvent_metadataEntries_EventIntMetadataEntry {
  __typename: "EventIntMetadataEntry";
  label: string;
  description: string | null;
  intValue: number;
}

export type LogsRowStructuredFragment_EngineEvent_metadataEntries = LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventTextMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry | LogsRowStructuredFragment_EngineEvent_metadataEntries_EventIntMetadataEntry;

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
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: LogsRowStructuredFragment_HookErroredEvent_error;
}

export type LogsRowStructuredFragment = LogsRowStructuredFragment_ExecutionStepSkippedEvent | LogsRowStructuredFragment_StepMaterializationEvent | LogsRowStructuredFragment_PipelineInitFailureEvent | LogsRowStructuredFragment_PipelineFailureEvent | LogsRowStructuredFragment_ExecutionStepFailureEvent | LogsRowStructuredFragment_ExecutionStepInputEvent | LogsRowStructuredFragment_ExecutionStepOutputEvent | LogsRowStructuredFragment_StepExpectationResultEvent | LogsRowStructuredFragment_ObjectStoreOperationEvent | LogsRowStructuredFragment_EngineEvent | LogsRowStructuredFragment_HookErroredEvent;
