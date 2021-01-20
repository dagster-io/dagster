// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DaemonType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SchedulerInfoQuery
// ====================================================

export interface SchedulerInfoQuery_scheduler_SchedulerNotDefinedError {
  __typename: "SchedulerNotDefinedError";
  message: string;
}

export interface SchedulerInfoQuery_scheduler_Scheduler {
  __typename: "Scheduler";
  schedulerClass: string | null;
}

export interface SchedulerInfoQuery_scheduler_PythonError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerInfoQuery_scheduler_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerInfoQuery_scheduler_PythonError_cause | null;
}

export type SchedulerInfoQuery_scheduler = SchedulerInfoQuery_scheduler_SchedulerNotDefinedError | SchedulerInfoQuery_scheduler_Scheduler | SchedulerInfoQuery_scheduler_PythonError;

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatError_cause | null;
}

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: DaemonType;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatError: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatError | null;
  lastHeartbeatTime: number | null;
}

export interface SchedulerInfoQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface SchedulerInfoQuery_instance {
  __typename: "Instance";
  daemonHealth: SchedulerInfoQuery_instance_daemonHealth;
}

export interface SchedulerInfoQuery {
  scheduler: SchedulerInfoQuery_scheduler;
  instance: SchedulerInfoQuery_instance;
}
