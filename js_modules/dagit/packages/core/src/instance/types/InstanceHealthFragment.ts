/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: InstanceHealthFragment
// ====================================================

export interface InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  causes: InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_causes[];
}

export interface InstanceHealthFragment_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  id: string;
  daemonType: string;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceHealthFragment_daemonHealth {
  __typename: "DaemonHealth";
  id: string;
  allDaemonStatuses: InstanceHealthFragment_daemonHealth_allDaemonStatuses[];
}

export interface InstanceHealthFragment {
  __typename: "Instance";
  daemonHealth: InstanceHealthFragment_daemonHealth;
  hasInfo: boolean;
}
