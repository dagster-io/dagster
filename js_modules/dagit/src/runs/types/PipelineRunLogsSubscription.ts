// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel } from "./../../types/globalTypes";

// ====================================================
// GraphQL subscription operation: PipelineRunLogsSubscription
// ====================================================

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_LogMessageEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_LogMessageEvent {
  __typename: "LogMessageEvent" | "PipelineStartEvent" | "PipelineSuccessEvent" | "PipelineFailureEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepOutputEvent" | "ExecutionStepSkippedEvent" | "PipelineProcessStartEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_LogMessageEvent_step | null;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineInitFailureEvent_step | null;
  error: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineInitFailureEvent_error;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  stack: string[];
  message: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent_step | null;
  error: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent_error;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineProcessStartedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineProcessStartedEvent {
  __typename: "PipelineProcessStartedEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineProcessStartedEvent_step | null;
  processId: number;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  path: string | null;
  description: string | null;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepMaterializationEvent_step | null;
  materialization: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepMaterializationEvent_materialization;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  name: string | null;
  resultMetadataJsonString: string | null;
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  runId: string;
  message: string;
  timestamp: string;
  level: LogLevel;
  step: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepExpectationResultEvent_step | null;
  expectationResult: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepExpectationResultEvent_expectationResult;
}

export type PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages = PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_LogMessageEvent | PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineInitFailureEvent | PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_ExecutionStepFailureEvent | PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_PipelineProcessStartedEvent | PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepMaterializationEvent | PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages_StepExpectationResultEvent;

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess {
  __typename: "PipelineRunLogsSubscriptionSuccess";
  messages: PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess_messages[];
}

export interface PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionMissingRunIdFailure {
  __typename: "PipelineRunLogsSubscriptionMissingRunIdFailure";
  missingRunId: string;
}

export type PipelineRunLogsSubscription_pipelineRunLogs = PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionSuccess | PipelineRunLogsSubscription_pipelineRunLogs_PipelineRunLogsSubscriptionMissingRunIdFailure;

export interface PipelineRunLogsSubscription {
  pipelineRunLogs: PipelineRunLogsSubscription_pipelineRunLogs;
}

export interface PipelineRunLogsSubscriptionVariables {
  runId: string;
  after?: any | null;
}
