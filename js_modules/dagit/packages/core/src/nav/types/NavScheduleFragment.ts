// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: NavScheduleFragment
// ====================================================

export interface NavScheduleFragment_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface NavScheduleFragment {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  scheduleState: NavScheduleFragment_scheduleState;
}
