// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PipelineRunLogsSubscriptionStatusFragment
// ====================================================

export interface PipelineRunLogsSubscriptionStatusFragment {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  canTerminate: boolean;
}
