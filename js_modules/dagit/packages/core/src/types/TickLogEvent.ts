/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { LogLevel } from "./globalTypes";

// ====================================================
// GraphQL fragment: TickLogEvent
// ====================================================

export interface TickLogEvent {
  __typename: "InstigationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
}
