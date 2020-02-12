// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ScheduleStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: StartSchedule
// ====================================================

export interface StartSchedule_startSchedule_schedule_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
}

export interface StartSchedule_startSchedule_schedule {
  __typename: "RunningSchedule";
  scheduleDefinition: StartSchedule_startSchedule_schedule_scheduleDefinition;
  status: ScheduleStatus;
}

export interface StartSchedule_startSchedule {
  __typename: "RunningScheduleResult";
  schedule: StartSchedule_startSchedule_schedule;
}

export interface StartSchedule {
  startSchedule: StartSchedule_startSchedule;
}

export interface StartScheduleVariables {
  scheduleName: string;
}
