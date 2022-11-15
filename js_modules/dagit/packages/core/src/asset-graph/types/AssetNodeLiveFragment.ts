/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: AssetNodeLiveFragment
// ====================================================

export interface AssetNodeLiveFragment_repository {
  __typename: "Repository";
  id: string;
}

export interface AssetNodeLiveFragment_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetNodeLiveFragment_assetMaterializations {
  __typename: "MaterializationEvent";
  timestamp: string;
  runId: string;
}

export interface AssetNodeLiveFragment_freshnessPolicy {
  __typename: "FreshnessPolicy";
  maximumLagMinutes: number;
  cronSchedule: string | null;
}

export interface AssetNodeLiveFragment_freshnessInfo {
  __typename: "AssetFreshnessInfo";
  currentMinutesLate: number | null;
}

export interface AssetNodeLiveFragment_assetObservations {
  __typename: "ObservationEvent";
  timestamp: string;
  runId: string;
}

export interface AssetNodeLiveFragment {
  __typename: "AssetNode";
  id: string;
  opNames: string[];
  repository: AssetNodeLiveFragment_repository;
  assetKey: AssetNodeLiveFragment_assetKey;
  assetMaterializations: AssetNodeLiveFragment_assetMaterializations[];
  freshnessPolicy: AssetNodeLiveFragment_freshnessPolicy | null;
  freshnessInfo: AssetNodeLiveFragment_freshnessInfo | null;
  assetObservations: AssetNodeLiveFragment_assetObservations[];
  currentLogicalVersion: string | null;
  projectedLogicalVersion: string | null;
}
