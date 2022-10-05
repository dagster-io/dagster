/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL subscription operation: AssetLogEventsSubscription
// ====================================================

export interface AssetLogEventsSubscription_assetLogEvents_events_ObservationEvent {
  __typename: "ObservationEvent";
}

export interface AssetLogEventsSubscription_assetLogEvents_events_MaterializationEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLogEventsSubscription_assetLogEvents_events_MaterializationEvent {
  __typename: "MaterializationEvent";
  timestamp: string;
  runId: string;
  assetKey: AssetLogEventsSubscription_assetLogEvents_events_MaterializationEvent_assetKey | null;
}

export interface AssetLogEventsSubscription_assetLogEvents_events_ExecutionStepStartEvent {
  __typename: "ExecutionStepStartEvent";
  timestamp: string;
  stepKey: string | null;
  runId: string;
}

export interface AssetLogEventsSubscription_assetLogEvents_events_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  timestamp: string;
  stepKey: string | null;
  runId: string;
}

export interface AssetLogEventsSubscription_assetLogEvents_events_AssetMaterializationPlannedEvent_assetKey {
  __typename: "AssetKey";
  path: string[];
}

export interface AssetLogEventsSubscription_assetLogEvents_events_AssetMaterializationPlannedEvent {
  __typename: "AssetMaterializationPlannedEvent";
  timestamp: string;
  runId: string;
  assetKey: AssetLogEventsSubscription_assetLogEvents_events_AssetMaterializationPlannedEvent_assetKey | null;
}

export type AssetLogEventsSubscription_assetLogEvents_events = AssetLogEventsSubscription_assetLogEvents_events_ObservationEvent | AssetLogEventsSubscription_assetLogEvents_events_MaterializationEvent | AssetLogEventsSubscription_assetLogEvents_events_ExecutionStepStartEvent | AssetLogEventsSubscription_assetLogEvents_events_ExecutionStepFailureEvent | AssetLogEventsSubscription_assetLogEvents_events_AssetMaterializationPlannedEvent;

export interface AssetLogEventsSubscription_assetLogEvents {
  __typename: "AssetLogEventsSubscription";
  events: AssetLogEventsSubscription_assetLogEvents_events[];
}

export interface AssetLogEventsSubscription {
  assetLogEvents: AssetLogEventsSubscription_assetLogEvents;
}
