// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunPipelineRunEventFragment
// ====================================================

export interface RunPipelineRunEventFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "HookCompletedEvent" | "HookSkippedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries = RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry | RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventFloatMetadataEntry;

export interface RunPipelineRunEventFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  assetKey: RunPipelineRunEventFragment_StepMaterializationEvent_materialization_assetKey | null;
  label: string;
  description: string | null;
  metadataEntries: RunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface RunPipelineRunEventFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  materialization: RunPipelineRunEventFragment_StepMaterializationEvent_materialization;
}

export interface RunPipelineRunEventFragment_PipelineInitFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunPipelineRunEventFragment_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunPipelineRunEventFragment_PipelineInitFailureEvent_error_cause | null;
}

export interface RunPipelineRunEventFragment_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: RunPipelineRunEventFragment_PipelineInitFailureEvent_error;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunPipelineRunEventFragment_ExecutionStepFailureEvent_error_cause | null;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry | RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry | RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry | RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry | RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry | RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry | RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventFloatMetadataEntry;

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface RunPipelineRunEventFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: RunPipelineRunEventFragment_ExecutionStepFailureEvent_error;
  failureMetadata: RunPipelineRunEventFragment_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry;

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface RunPipelineRunEventFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  inputName: string;
  typeCheck: RunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck;
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry | RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventFloatMetadataEntry;

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface RunPipelineRunEventFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  outputName: string;
  typeCheck: RunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck;
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries = RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry | RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry | RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventFloatMetadataEntry;

export interface RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface RunPipelineRunEventFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  expectationResult: RunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult;
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry | RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventFloatMetadataEntry;

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface RunPipelineRunEventFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  operationResult: RunPipelineRunEventFragment_ObjectStoreOperationEvent_operationResult;
}

export interface RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export interface RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry {
  __typename: "EventFloatMetadataEntry";
  label: string;
  description: string | null;
  value: number;
}

export type RunPipelineRunEventFragment_EngineEvent_metadataEntries = RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventPathMetadataEntry | RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry | RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry | RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventTextMetadataEntry | RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry | RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry | RunPipelineRunEventFragment_EngineEvent_metadataEntries_EventFloatMetadataEntry;

export interface RunPipelineRunEventFragment_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunPipelineRunEventFragment_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunPipelineRunEventFragment_EngineEvent_engineError_cause | null;
}

export interface RunPipelineRunEventFragment_EngineEvent {
  __typename: "EngineEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  metadataEntries: RunPipelineRunEventFragment_EngineEvent_metadataEntries[];
  engineError: RunPipelineRunEventFragment_EngineEvent_engineError | null;
  markerStart: string | null;
  markerEnd: string | null;
}

export interface RunPipelineRunEventFragment_HookErroredEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunPipelineRunEventFragment_HookErroredEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunPipelineRunEventFragment_HookErroredEvent_error_cause | null;
}

export interface RunPipelineRunEventFragment_HookErroredEvent {
  __typename: "HookErroredEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  stepKey: string | null;
  error: RunPipelineRunEventFragment_HookErroredEvent_error;
}

export type RunPipelineRunEventFragment = RunPipelineRunEventFragment_ExecutionStepSkippedEvent | RunPipelineRunEventFragment_StepMaterializationEvent | RunPipelineRunEventFragment_PipelineInitFailureEvent | RunPipelineRunEventFragment_ExecutionStepFailureEvent | RunPipelineRunEventFragment_ExecutionStepInputEvent | RunPipelineRunEventFragment_ExecutionStepOutputEvent | RunPipelineRunEventFragment_StepExpectationResultEvent | RunPipelineRunEventFragment_ObjectStoreOperationEvent | RunPipelineRunEventFragment_EngineEvent | RunPipelineRunEventFragment_HookErroredEvent;
