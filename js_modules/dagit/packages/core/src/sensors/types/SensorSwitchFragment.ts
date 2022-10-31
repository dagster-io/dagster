/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: SensorSwitchFragment
// ====================================================

export interface SensorSwitchFragment_sensorState {
  __typename: "InstigationState";
  id: string;
  selectorId: string;
  status: InstigationStatus;
}

export interface SensorSwitchFragment {
  __typename: "Sensor";
  id: string;
  jobOriginId: string;
  name: string;
  sensorState: SensorSwitchFragment_sensorState;
}
