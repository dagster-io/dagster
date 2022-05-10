/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { BulkActionStatus, RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: BackfillTableFragment
// ====================================================

export interface BackfillTableFragment_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface BackfillTableFragment_runs {
  __typename: "Run";
  id: string;
  canTerminate: boolean;
  status: RunStatus;
  tags: BackfillTableFragment_runs_tags[];
}

export interface BackfillTableFragment_partitionSet_repositoryOrigin {
  __typename: "RepositoryOrigin";
  id: string;
  repositoryName: string;
  repositoryLocationName: string;
}

export interface BackfillTableFragment_partitionSet {
  __typename: "PartitionSet";
  id: string;
  name: string;
  mode: string;
  pipelineName: string;
  repositoryOrigin: BackfillTableFragment_partitionSet_repositoryOrigin;
}

export interface BackfillTableFragment_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface BackfillTableFragment_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: BackfillTableFragment_error_cause | null;
}

export interface BackfillTableFragment {
  __typename: "PartitionBackfill";
  backfillId: string;
  status: BulkActionStatus;
  numRequested: number;
  partitionNames: string[];
  runs: BackfillTableFragment_runs[];
  timestamp: number;
  partitionSetName: string;
  partitionSet: BackfillTableFragment_partitionSet | null;
  error: BackfillTableFragment_error | null;
}
