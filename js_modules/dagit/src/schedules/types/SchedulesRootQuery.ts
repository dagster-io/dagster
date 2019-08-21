// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SchedulesRootQuery
// ====================================================

export interface SchedulesRootQuery_schedules {
  __typename: "ScheduleDefinition";
  name: string;
  executionParamsString: string;
  cronSchedule: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules_scheduleDefinition {
  __typename: "ScheduleDefinition";
  name: string;
}

export interface SchedulesRootQuery_scheduler_Scheduler_runningSchedules {
  __typename: "RunningSchedule";
  scheduleDefinition: SchedulesRootQuery_scheduler_Scheduler_runningSchedules_scheduleDefinition;
}

export interface SchedulesRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  runningSchedules: SchedulesRootQuery_scheduler_Scheduler_runningSchedules[];
}

export interface SchedulesRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export type SchedulesRootQuery_scheduler = SchedulesRootQuery_scheduler_Scheduler | SchedulesRootQuery_scheduler_SchedulerNotDefinedError;

export interface SchedulesRootQuery {
  schedules: SchedulesRootQuery_schedules[];
  scheduler: SchedulesRootQuery_scheduler;
}
