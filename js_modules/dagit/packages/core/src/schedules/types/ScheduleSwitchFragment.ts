// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleSwitchFragment
// ====================================================

export interface ScheduleSwitchFragment_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface ScheduleSwitchFragment {
  __typename: "Schedule";
  id: string;
  name: string;
  scheduleState: ScheduleSwitchFragment_scheduleState;
}
