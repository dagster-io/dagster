/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionStepStatusRun
// ====================================================

export interface PartitionStepStatusRun_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionStepStatusRun_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  status: StepEventStatus | null;
}

export interface PartitionStepStatusRun {
  __typename: "Run";
  id: string;
  runId: string;
  tags: PartitionStepStatusRun_tags[];
  stepStats: PartitionStepStatusRun_stepStats[];
}
