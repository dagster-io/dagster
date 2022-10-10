/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { AssetKeyInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL subscription operation: AssetLogEventsSubscription
// ====================================================

export interface AssetLogEventsSubscription_assetLogEvents_AssetLogEventsSubscriptionSuccess_events {
  __typename: "MaterializationEvent" | "ObservationEvent" | "AssetMaterializationPlannedEvent";
}

export interface AssetLogEventsSubscription_assetLogEvents_AssetLogEventsSubscriptionSuccess {
  __typename: "AssetLogEventsSubscriptionSuccess";
  events: AssetLogEventsSubscription_assetLogEvents_AssetLogEventsSubscriptionSuccess_events[];
}

export interface AssetLogEventsSubscription_assetLogEvents_AssetLogEventsSubscriptionFailure {
  __typename: "AssetLogEventsSubscriptionFailure";
  message: string;
}

export type AssetLogEventsSubscription_assetLogEvents = AssetLogEventsSubscription_assetLogEvents_AssetLogEventsSubscriptionSuccess | AssetLogEventsSubscription_assetLogEvents_AssetLogEventsSubscriptionFailure;

export interface AssetLogEventsSubscription {
  assetLogEvents: AssetLogEventsSubscription_assetLogEvents;
}

export interface AssetLogEventsSubscriptionVariables {
  assetKeys: AssetKeyInput[];
}
