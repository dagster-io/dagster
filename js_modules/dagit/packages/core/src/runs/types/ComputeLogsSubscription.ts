/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { ComputeIOType } from "./../../types/globalTypes";

// ====================================================
// GraphQL subscription operation: ComputeLogsSubscription
// ====================================================

export interface ComputeLogsSubscription_computeLogs {
  __typename: "ComputeLogFile";
  path: string;
  cursor: number;
  data: string | null;
  downloadUrl: string | null;
}

export interface ComputeLogsSubscription {
  computeLogs: ComputeLogsSubscription_computeLogs;
}

export interface ComputeLogsSubscriptionVariables {
  runId: string;
  stepKey: string;
  ioType: ComputeIOType;
  cursor?: string | null;
}
