// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { JobStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: NavScheduleFragment
// ====================================================

export interface NavScheduleFragment_scheduleState {
  __typename: "JobState";
  id: string;
  status: JobStatus;
}

export interface NavScheduleFragment {
  __typename: "Schedule";
  id: string;
  mode: string;
  name: string;
  scheduleState: NavScheduleFragment_scheduleState;
}
