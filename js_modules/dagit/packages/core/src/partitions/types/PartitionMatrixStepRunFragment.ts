/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus, StepEventStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: PartitionMatrixStepRunFragment
// ====================================================

export interface PartitionMatrixStepRunFragment_stepStats {
  __typename: "RunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  status: StepEventStatus | null;
}

export interface PartitionMatrixStepRunFragment_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionMatrixStepRunFragment {
  __typename: "Run";
  id: string;
  runId: string;
  status: RunStatus;
  startTime: number | null;
  endTime: number | null;
  stepStats: PartitionMatrixStepRunFragment_stepStats[];
  tags: PartitionMatrixStepRunFragment_tags[];
}
