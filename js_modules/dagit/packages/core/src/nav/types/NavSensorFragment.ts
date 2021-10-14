// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: NavSensorFragment
// ====================================================

export interface NavSensorFragment_targets {
  __typename: "Target";
  mode: string;
  pipelineName: string;
}

export interface NavSensorFragment_sensorState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface NavSensorFragment {
  __typename: "Sensor";
  id: string;
  name: string;
  targets: NavSensorFragment_targets[] | null;
  sensorState: NavSensorFragment_sensorState;
}
