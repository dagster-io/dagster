// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsScrollingTableMessageFragment
// ====================================================

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineProcessStartEvent" | "PipelineProcessStartedEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "StepExpectationResultEvent" | "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface LogsScrollingTableMessageFragment_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface LogsScrollingTableMessageFragment_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  error: LogsScrollingTableMessageFragment_PipelineInitFailureEvent_error;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_step | null;
  error: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error;
}

export type LogsScrollingTableMessageFragment = LogsScrollingTableMessageFragment_ExecutionStepInputEvent | LogsScrollingTableMessageFragment_PipelineInitFailureEvent | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent;
