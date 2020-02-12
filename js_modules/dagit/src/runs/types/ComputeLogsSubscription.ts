// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ComputeIOType } from "./../../types/globalTypes";

// ====================================================
// GraphQL subscription operation: ComputeLogsSubscription
// ====================================================

export interface ComputeLogsSubscription_computeLogs {
  __typename: "ComputeLogFile";
  data: string;
  cursor: number;
  path: string;
  downloadUrl: string;
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
