/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { LocationStateChangeEventType } from "./../../types/globalTypes";

// ====================================================
// GraphQL subscription operation: LocationStateChangeSubscription
// ====================================================

export interface LocationStateChangeSubscription_locationStateChangeEvents_event {
  __typename: "LocationStateChangeEvent";
  message: string;
  locationName: string;
  eventType: LocationStateChangeEventType;
  serverId: string | null;
}

export interface LocationStateChangeSubscription_locationStateChangeEvents {
  __typename: "LocationStateChangeSubscription";
  event: LocationStateChangeSubscription_locationStateChangeEvents_event;
}

export interface LocationStateChangeSubscription {
  locationStateChangeEvents: LocationStateChangeSubscription_locationStateChangeEvents;
}
