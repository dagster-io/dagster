// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunPipelineRunEventFragment
// ====================================================

export interface PipelineRunPipelineRunEventFragment_LogMessageEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_LogMessageEvent_step | null;
}

export interface PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  error: PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_error;
  step: PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent_step | null;
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

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  path: string | null;
  description: string | null;
}

export interface PipelineRunPipelineRunEventFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_StepMaterializationEvent_step | null;
  materialization: PipelineRunPipelineRunEventFragment_StepMaterializationEvent_materialization;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  name: string | null;
  resultMetadataJsonString: string | null;
}

export interface PipelineRunPipelineRunEventFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_step | null;
  expectationResult: PipelineRunPipelineRunEventFragment_StepExpectationResultEvent_expectationResult;
}

export type PipelineRunPipelineRunEventFragment = PipelineRunPipelineRunEventFragment_LogMessageEvent | PipelineRunPipelineRunEventFragment_PipelineInitFailureEvent | PipelineRunPipelineRunEventFragment_ExecutionStepFailureEvent | PipelineRunPipelineRunEventFragment_PipelineProcessStartedEvent | PipelineRunPipelineRunEventFragment_StepMaterializationEvent | PipelineRunPipelineRunEventFragment_StepExpectationResultEvent;
