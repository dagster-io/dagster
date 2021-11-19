/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { RunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: RunMetadataFragment
// ====================================================

export interface RunMetadataFragment_assets_key {
  __typename: "AssetKey";
  path: string[];
}

export interface RunMetadataFragment_assets {
  __typename: "Asset";
  id: string;
  key: RunMetadataFragment_assets_key;
}

export interface RunMetadataFragment_stats_RunStatsSnapshot {
  __typename: "RunStatsSnapshot";
  id: string;
  enqueuedTime: number | null;
  launchTime: number | null;
  startTime: number | null;
  endTime: number | null;
}

export interface RunMetadataFragment_stats_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface RunMetadataFragment_stats_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: RunMetadataFragment_stats_PythonError_cause | null;
}

export type RunMetadataFragment_stats = RunMetadataFragment_stats_RunStatsSnapshot | RunMetadataFragment_stats_PythonError;

export interface RunMetadataFragment {
  __typename: "Run";
  id: string;
  status: RunStatus;
  assets: RunMetadataFragment_assets[];
  stats: RunMetadataFragment_stats;
}
