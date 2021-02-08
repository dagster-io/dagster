// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

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

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: SchedulerInfoQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
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
