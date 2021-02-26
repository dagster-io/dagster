// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: InstanceWarningQuery
// ====================================================

export interface InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string | null;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceWarningQuery_instance_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: InstanceWarningQuery_instance_daemonHealth_allDaemonStatuses[];
}

export interface InstanceWarningQuery_instance {
  __typename: "Instance";
  daemonHealth: InstanceWarningQuery_instance_daemonHealth;
}

export interface InstanceWarningQuery {
  instance: InstanceWarningQuery_instance;
}
