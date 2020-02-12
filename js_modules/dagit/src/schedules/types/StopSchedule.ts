// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StopSchedule
// ====================================================

export interface StopSchedule_stopRunningSchedule_schedule_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
}

export interface StopSchedule_stopRunningSchedule_schedule {
  __typename: "RunningSchedule";
  scheduleDefinition: StopSchedule_stopRunningSchedule_schedule_scheduleDefinition;
  status: ScheduleStatus;
}

export interface StopSchedule_stopRunningSchedule {
  __typename: "RunningScheduleResult";
  schedule: StopSchedule_stopRunningSchedule_schedule;
}

export interface StopSchedule {
  stopRunningSchedule: StopSchedule_stopRunningSchedule;
}

export interface StopScheduleVariables {
  scheduleName: string;
}
