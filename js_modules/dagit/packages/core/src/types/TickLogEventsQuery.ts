/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationSelector, InstigationTickStatus, LogLevel } from "./globalTypes";

// ====================================================
// GraphQL query operation: TickLogEventsQuery
// ====================================================

export interface TickLogEventsQuery_instigationStateOrError_InstigationStateNotFoundError {
  __typename: "InstigationStateNotFoundError" | "PythonError";
}

export interface TickLogEventsQuery_instigationStateOrError_InstigationState_tick_logEvents_events {
  __typename: "InstigationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}

export interface TickLogEventsQuery_instigationStateOrError_InstigationState_tick_logEvents {
  __typename: "InstigationEventConnection";
  events: TickLogEventsQuery_instigationStateOrError_InstigationState_tick_logEvents_events[];
}

export interface TickLogEventsQuery_instigationStateOrError_InstigationState_tick {
  __typename: "InstigationTick";
  id: string;
  status: InstigationTickStatus;
  timestamp: number;
  logEvents: TickLogEventsQuery_instigationStateOrError_InstigationState_tick_logEvents;
}

export interface TickLogEventsQuery_instigationStateOrError_InstigationState {
  __typename: "InstigationState";
  id: string;
  tick: TickLogEventsQuery_instigationStateOrError_InstigationState_tick | null;
}

export type TickLogEventsQuery_instigationStateOrError = TickLogEventsQuery_instigationStateOrError_InstigationStateNotFoundError | TickLogEventsQuery_instigationStateOrError_InstigationState;

export interface TickLogEventsQuery {
  instigationStateOrError: TickLogEventsQuery_instigationStateOrError;
}

export interface TickLogEventsQueryVariables {
  instigationSelector: InstigationSelector;
  timestamp: number;
}
