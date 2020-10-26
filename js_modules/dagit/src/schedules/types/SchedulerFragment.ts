// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: SchedulerFragment
// ====================================================

export interface SchedulerFragment_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulerFragment_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface SchedulerFragment_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerFragment_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerFragment_PythonError_cause | null;
}

export type SchedulerFragment = SchedulerFragment_SchedulerNotDefinedError | SchedulerFragment_Scheduler | SchedulerFragment_PythonError;
