/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SingleBackfillQuery
// ====================================================

export interface SingleBackfillQuery_partitionBackfillOrError_PythonError {
  __typename: "PythonError";
}

export interface SingleBackfillQuery_partitionBackfillOrError_PartitionBackfill_partitionStatuses_results {
  __typename: "PartitionStatus";
  id: string;
  partitionName: string;
  runId: string | null;
  runStatus: RunStatus | null;
}

export interface SingleBackfillQuery_partitionBackfillOrError_PartitionBackfill_partitionStatuses {
  __typename: "PartitionStatuses";
  results: SingleBackfillQuery_partitionBackfillOrError_PartitionBackfill_partitionStatuses_results[];
}

export interface SingleBackfillQuery_partitionBackfillOrError_PartitionBackfill {
  __typename: "PartitionBackfill";
  partitionStatuses: SingleBackfillQuery_partitionBackfillOrError_PartitionBackfill_partitionStatuses;
}

export type SingleBackfillQuery_partitionBackfillOrError = SingleBackfillQuery_partitionBackfillOrError_PythonError | SingleBackfillQuery_partitionBackfillOrError_PartitionBackfill;

export interface SingleBackfillQuery {
  partitionBackfillOrError: SingleBackfillQuery_partitionBackfillOrError;
}

export interface SingleBackfillQueryVariables {
  backfillId: string;
}
