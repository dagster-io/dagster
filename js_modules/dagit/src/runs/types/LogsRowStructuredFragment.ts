// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsRowStructuredFragment
// ====================================================

export interface LogsRowStructuredFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
}

export interface LogsRowStructuredFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  processId: number;
}

export interface LogsRowStructuredFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
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

export type LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries = LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry;

export interface LogsRowStructuredFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface LogsRowStructuredFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  step: LogsRowStructuredFragment_StepMaterializationEvent_step | null;
  materialization: LogsRowStructuredFragment_StepMaterializationEvent_materialization;
}

export interface LogsRowStructuredFragment_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface LogsRowStructuredFragment_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  error: LogsRowStructuredFragment_PipelineInitFailureEvent_error;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface LogsRowStructuredFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  level: LogLevel;
  step: LogsRowStructuredFragment_ExecutionStepFailureEvent_step | null;
  error: LogsRowStructuredFragment_ExecutionStepFailureEvent_error;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries {
  __typename: "EventJsonMetadataEntry" | "EventPathMetadataEntry" | "EventTextMetadataEntry" | "EventUrlMetadataEntry";
  label: string;
  description: string | null;
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  inputName: string;
  valueRepr: string;
  typeCheck: LogsRowStructuredFragment_ExecutionStepInputEvent_typeCheck;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries {
  __typename: "EventJsonMetadataEntry" | "EventPathMetadataEntry" | "EventTextMetadataEntry" | "EventUrlMetadataEntry";
  label: string;
  description: string | null;
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: LogsRowStructuredFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface LogsRowStructuredFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  outputName: string;
  valueRepr: string;
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

export type LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries = LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry;

export interface LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface LogsRowStructuredFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  expectationResult: LogsRowStructuredFragment_StepExpectationResultEvent_expectationResult;
}

export type LogsRowStructuredFragment = LogsRowStructuredFragment_ExecutionStepSkippedEvent | LogsRowStructuredFragment_PipelineProcessStartedEvent | LogsRowStructuredFragment_StepMaterializationEvent | LogsRowStructuredFragment_PipelineInitFailureEvent | LogsRowStructuredFragment_ExecutionStepFailureEvent | LogsRowStructuredFragment_ExecutionStepInputEvent | LogsRowStructuredFragment_ExecutionStepOutputEvent | LogsRowStructuredFragment_StepExpectationResultEvent;
