// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SchedulerRootQuery
// ====================================================

export interface SchedulerRootQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulerRootQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface SchedulerRootQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerRootQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerRootQuery_scheduler_PythonError_cause | null;
}

export type SchedulerRootQuery_scheduler = SchedulerRootQuery_scheduler_SchedulerNotDefinedError | SchedulerRootQuery_scheduler_Scheduler | SchedulerRootQuery_scheduler_PythonError;

export interface SchedulerRootQuery {
  scheduler: SchedulerRootQuery_scheduler;
}
