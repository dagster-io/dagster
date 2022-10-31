/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { InstigationStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ScheduleFutureTicksFragment
// ====================================================

export interface ScheduleFutureTicksFragment_scheduleState {
  __typename: "InstigationState";
  id: string;
  status: InstigationStatus;
}

export interface ScheduleFutureTicksFragment_futureTicks_results {
  __typename: "FutureInstigationTick";
  timestamp: number;
}

export interface ScheduleFutureTicksFragment_futureTicks {
  __typename: "FutureInstigationTicks";
  results: ScheduleFutureTicksFragment_futureTicks_results[];
}

export interface ScheduleFutureTicksFragment {
  __typename: "Schedule";
  id: string;
  executionTimezone: string | null;
  scheduleState: ScheduleFutureTicksFragment_scheduleState;
  futureTicks: ScheduleFutureTicksFragment_futureTicks;
}
