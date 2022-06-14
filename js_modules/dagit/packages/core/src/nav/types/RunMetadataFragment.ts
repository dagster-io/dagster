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
  __typename: "MaterializedKey";
  id: string;
  key: RunMetadataFragment_assets_key;
}

export interface RunMetadataFragment {
  __typename: "Run";
  id: string;
  status: RunStatus;
  assets: RunMetadataFragment_assets[];
  runId: string;
  startTime: number | null;
  endTime: number | null;
  updateTime: number | null;
}
