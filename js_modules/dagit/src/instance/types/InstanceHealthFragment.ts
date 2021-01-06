// @generated
/* tslint:disable */
/* eslint-disable */
// @generated
// This file was automatically generated and should not be edited.

import { DaemonType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: InstanceHealthFragment
// ====================================================

export interface InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors_cause | null;
}

export interface InstanceHealthFragment_daemonHealth_allDaemonStatuses {
  __typename: "DaemonStatus";
  daemonType: DaemonType;
  required: boolean;
  healthy: boolean | null;
  lastHeartbeatErrors: InstanceHealthFragment_daemonHealth_allDaemonStatuses_lastHeartbeatErrors[];
  lastHeartbeatTime: number | null;
}

export interface InstanceHealthFragment_daemonHealth {
  __typename: "DaemonHealth";
  allDaemonStatuses: InstanceHealthFragment_daemonHealth_allDaemonStatuses[];
}

export interface InstanceHealthFragment {
  __typename: "Instance";
  daemonHealth: InstanceHealthFragment_daemonHealth;
}
