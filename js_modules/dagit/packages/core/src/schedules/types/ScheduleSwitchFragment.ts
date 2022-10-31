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
  selectorId: string;
  status: InstigationStatus;
}

export interface ScheduleSwitchFragment {
  __typename: "Schedule";
  id: string;
  name: string;
  cronSchedule: string;
  executionTimezone: string | null;
  scheduleState: ScheduleSwitchFragment_scheduleState;
}
