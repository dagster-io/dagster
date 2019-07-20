// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunPipelineRunEventFragment
// ====================================================

export interface PipelineRunPipelineRunEventFragment_ExecutionStepSkippedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_ExecutionStepSkippedEvent_step | null;
}

export interface PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunPipelineRunEventFragment_PipelineProcessStartEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_PipelineProcessStartEvent {
  __typename: "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_PipelineProcessStartEvent_step | null;
  pipelineName: string;
  runId: string;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries = PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_StepMaterializationEvent_step | null;
  materialization: PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization;
}

export interface PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_step | null;
  error: PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_error;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_step | null;
  error: PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent_error;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_step_inputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_step_inputs {
  __typename: "ExecutionStepInput";
  name: string;
  type: PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_step_inputs_type;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  inputs: PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_step_inputs[];
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_step | null;
  inputName: string;
  typeCheck: PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent_typeCheck;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_step_outputs_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  displayName: string;
  description: string | null;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_step_outputs {
  __typename: "ExecutionStepOutput";
  name: string;
  type: PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_step_outputs_type;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_step {
  __typename: "ExecutionStep";
  key: string;
  outputs: PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_step_outputs[];
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_step | null;
  outputName: string;
  typeCheck: PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent_typeCheck;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export type PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries = PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry;

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_step | null;
  expectationResult: PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult;
}

export type PipelineRunPipelineRunEventFragment = PipelineRunPipelineRunEventFragment_ExecutionStepSkippedEvent | PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent | PipelineRunPipelineRunEventFragment_PipelineProcessStartEvent | PipelineRunPipelineRunEventFragment_StepMaterializationEvent | PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent | PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineRunPipelineRunEventFragment_ExecutionStepInputEvent | PipelineRunPipelineRunEventFragment_ExecutionStepOutputEvent | PipelineRunPipelineRunEventFragment_StepExpectationResultEvent;
